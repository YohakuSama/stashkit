#!/usr/bin/env python3
"""Build private Stash selectors from an existing local Clash/Stash node config.

Node names and provider names are discovered from the input; neither needs a
hardcoded name. Output contains private node credentials and must not be
committed to the repository.
"""
import argparse
import copy
import os
import tempfile
from pathlib import Path

import yaml

from node_sources import load_private_yaml, resolve_node_sources, subscription_url
from validate_config import validate_profile

ROOT = Path(__file__).resolve().parents[1]
NODE_POOLS = frozenset({"Proxy", "Auto", "Fallback", "ALL"})
SERVICE_EXCEPTIONS = frozenset({"AdBlock", "Final"})
EXPECTED_GROUP_COUNT = 40
# Public profiles use a dedicated dynamic node pool. Flat private output expands
# real nodes instead of depending on Stash merging proxies with use/include-all.
PROFILE_FILES = {
    "default": "StashKit.yaml",
    "privacy": "StashKit-Privacy.yaml",
    "local": "StashKit-Local.yaml",
}
NATIVE_PROFILE_FILES = {
    "default": "StashKit.yaml",
    "privacy": "StashKit-Privacy.yaml",
    "local": "StashKit-Local.yaml",
}


def read_node_sources(path):
    """Read node entries and provider definitions without modifying user input."""
    data = load_private_yaml(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("Expected a Clash/Stash YAML mapping")
    nodes = data.get("proxies") or []
    providers = data.get("proxy-providers") or {}
    if not isinstance(nodes, list) or not isinstance(providers, dict):
        raise ValueError("proxies must be a list and proxy-providers must be a mapping")
    if not nodes and not providers:
        raise ValueError("Input contains no named nodes or proxy-providers")
    names = []
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("name"), str) or not node["name"]:
            raise ValueError("Every local proxy must have a nonempty name")
        names.append(node["name"])
    if len(names) != len(set(names)):
        raise ValueError("Duplicate local node names")
    for name, spec in providers.items():
        if not isinstance(name, str) or not name or not isinstance(spec, dict):
            raise ValueError("Invalid proxy-provider definition")
        url = spec.get("url", "")
        if not isinstance(url, str) or "example.invalid" in url or "REPLACE-" in url:
            raise ValueError("Replace placeholder provider URLs before generation")
    return nodes, providers


def read_provider_override(path):
    """Backwards-compatible named-provider input for existing local workflows."""
    data = load_private_yaml(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or set(data) - {"name", "desc", "proxy-providers"}:
        raise ValueError("Expected an override containing only proxy-providers and optional metadata")
    nodes, providers = read_node_sources(path)
    if nodes or not providers:
        raise ValueError("At least one named proxy provider is required")
    return providers


def read_subscription_urls(path):
    """Read private subscription URLs without printing or committing them."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    urls = [row.strip() for row in lines if row.strip()]
    if not urls or len(urls) != len(set(urls)):
        raise ValueError("Subscription URL file must contain unique nonempty URLs")
    for url in urls:
        subscription_url(url)
    return urls


def build_loon_selection(source, providers=None, nodes=None, subscription_urls=None,
                         layout="nested"):
    """Build either the safe nested layout or an experimental flat native layout.

    In native layout, Stash must merge named policy children and dynamic
    provider nodes in its iOS selector. Syntax validation cannot prove that UI
    behavior; use the native variant only for an explicit device experiment.
    """
    providers = copy.deepcopy(providers or {})
    nodes = copy.deepcopy(nodes or [])
    subscription_urls = list(subscription_urls or [])
    if layout not in {"nested", "native"}:
        raise ValueError("layout must be nested or native")
    if not providers and not nodes and not subscription_urls:
        raise ValueError("Named nodes or providers or subscription URLs are required")
    if subscription_urls and (providers or nodes):
        raise ValueError("Subscription URLs cannot be mixed with inline nodes or named providers")
    if len(subscription_urls) != len(set(subscription_urls)):
        raise ValueError("Duplicate subscription URLs")
    output = copy.deepcopy(source)
    groups = output["proxy-groups"]
    # Private profiles preserve the dedicated ALL node pool.
    manual = [group for group in groups if group["name"] == "Manual"]
    if manual:
        if (len(manual) != 1 or not manual[0].get("hidden")
                or not manual[0].get("include-all")):
            raise ValueError("Unexpected manual node pool structure")
        groups[:] = [group for group in groups if group["name"] != "Manual"]
    names = [group["name"] for group in groups]
    if len(set(names)) != len(groups) or "Manual" in names:
        raise ValueError("Unexpected canonical group structure")
    if layout == "nested":
        if len(groups) != EXPECTED_GROUP_COUNT or not NODE_POOLS.issubset(names):
            raise ValueError("Unexpected canonical group structure")
    elif (not {"Proxy", "Auto", "Fallback"}.issubset(names) or
          not ((len(groups) == EXPECTED_GROUP_COUNT - 1 and "ALL" not in names)
               or (len(groups) == EXPECTED_GROUP_COUNT and
                   NODE_POOLS.issubset(names)))):
        # Native generation accepts either the old ALL backup or the
        # published native profile, removing ALL only when present.
        raise ValueError("Unexpected canonical group structure")
    # Published native profiles declare only a local path-only Provider.
    canonical_providers = source.get("proxy-providers") or {}
    if (source.get("proxies") or
        (canonical_providers and
         not (layout == "native" and canonical_providers ==
              {"personal": {"path": "./providers/personal.yaml"}}))):
        raise ValueError("Canonical profile must not bundle personal nodes/providers")
    output.pop("proxy-providers", None)
    local_names = [node["name"] for node in nodes]
    if len(local_names) != len(set(local_names)):
        raise ValueError("Duplicate node names")
    if set(local_names) & (set(names) | {"DIRECT", "REJECT", "REJECT-DROP"}):
        raise ValueError("Node names conflict with strategy group names")
    if set(providers) & set(names):
        raise ValueError("Provider names conflict with strategy group names")

    if layout == "native":
        # The single-level experiment does not need ALL. Remove every ALL
        # reference, then attach the source directly to user-facing selectors.
        groups[:] = [group for group in groups if group["name"] != "ALL"]

    for group in groups:
        name = group["name"]
        if group["type"] not in {"select", "url-test", "fallback"}:
            raise ValueError(f"Unexpected group type: {name}")
        group.pop("include-all", None)
        group.pop("filter", None)
        if name == "Proxy":
            # Keep REJECT explicit: Stash documents that an empty provider
            # can resolve to DIRECT, so never silently use DIRECT as a policy.
            group["proxies"] = (["Auto", "Fallback"] + local_names + ["REJECT"]
                                if layout == "native"
                                else ["Auto", "Fallback", "ALL", "REJECT"])
        elif name in {"Auto", "Fallback", "ALL"}:
            # A node pool contains only nodes. REJECT is a manual policy on
            # Proxy/AdBlock, not a server to test or a fallback candidate.
            group["proxies"] = local_names[:]
        elif layout == "native" and name not in SERVICE_EXCEPTIONS:
            group["proxies"] = [child for child in group["proxies"]
                                if child != "ALL"] + local_names

        # The normal layout only lets the three node pools import providers.
        # The native experiment tests Stash's documented 'proxies' + 'use'.
        dynamic_group = (name not in SERVICE_EXCEPTIONS
                         if layout == "native"
                         else name in {"Auto", "Fallback", "ALL"})
        if dynamic_group and providers:
            group["use"] = list(providers)
        else:
            group.pop("use", None)
        if dynamic_group and subscription_urls:
            group["use-url"] = subscription_urls
        else:
            group.pop("use-url", None)
    if nodes:
        output["proxies"] = nodes
    if providers:
        output["proxy-providers"] = providers
    validate_profile(output)
    return output


def build_flat_selection(source, providers=None, nodes=None, subscription_urls=None,
                         base_dir=Path("."), **resolver_options):
    """Resolve actual nodes before building the 39 original LoonKit groups."""
    resolved = resolve_node_sources(nodes, providers, subscription_urls,
                                    base_dir=base_dir, **resolver_options)
    return build_loon_selection(source, nodes=resolved, layout="native")


def write_private_profile(output_file, output):
    """Replace only a complete validated profile, with owner-only permissions."""
    validate_profile(output)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=output_file.parent,
                                         prefix=".stashkit-", delete=False) as stream:
            temporary = Path(stream.name)
            yaml.safe_dump(output, stream, sort_keys=False, allow_unicode=True)
        os.replace(temporary, output_file)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=PROFILE_FILES, default="default")
    parser.add_argument("--layout", choices=("flat", "nested", "native"), default="flat",
                        help="flat (default) expands real nodes; native retains dynamic provider references")
    origin = parser.add_mutually_exclusive_group(required=True)
    origin.add_argument("--nodes-from", type=Path,
                        help="Existing local Clash/Stash YAML: auto-discovers proxy names and providers")
    origin.add_argument("--provider-override", type=Path,
                        help="Legacy local override with proxy-providers definitions")
    origin.add_argument("--subscription-file", type=Path,
                        help="Local text file with HTTPS node subscription URLs, one per line")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    output_file = args.output.resolve()
    if ROOT in output_file.parents and ROOT / "dist" not in output_file.parents:
        raise ValueError("Write private profiles only under dist/ or outside the repository")
    input_file = args.nodes_from or args.provider_override or args.subscription_file
    if output_file == input_file.resolve():
        raise ValueError("Output must not overwrite the private input file")

    urls = []
    if args.nodes_from:
        nodes, providers = read_node_sources(args.nodes_from)
    elif args.subscription_file:
        nodes, providers = [], {}
        urls = read_subscription_urls(args.subscription_file)
    else:
        nodes, providers = [], read_provider_override(args.provider_override)
    source_files = PROFILE_FILES
    source = yaml.safe_load((ROOT / source_files[args.profile]).read_text(encoding="utf-8"))
    if args.layout == "flat":
        output = build_flat_selection(source, providers, nodes, urls,
                                      base_dir=input_file.resolve().parent)
    else:
        output = build_loon_selection(source, providers, nodes, urls, layout=args.layout)
    write_private_profile(output_file, output)
    print(f"Generated private profile from {len(nodes)} local nodes, "
          f"{len(providers)} providers and {len(urls)} direct subscription URL(s): "
          f"{output_file}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, yaml.YAMLError):
        # YAML/HTTP exceptions can include subscription credentials. Keep
        # diagnostics generic at this private-input command boundary.
        raise SystemExit("Generation failed: check private inputs, node names and output path locally") from None
