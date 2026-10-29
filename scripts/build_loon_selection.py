#!/usr/bin/env python3
"""Build private Stash selectors from an existing local Clash/Stash node config.

Node names and provider names are discovered from the input; neither needs a
hardcoded name. Output contains private node credentials and must not be
committed to the repository.
"""
import argparse
import copy
from pathlib import Path
from urllib.parse import urlsplit

import yaml

from validate_config import validate_profile

ROOT = Path(__file__).resolve().parents[1]
NODE_POOLS = frozenset({"Proxy", "Auto", "Fallback"})
SERVICE_EXCEPTIONS = frozenset({"AdBlock", "Final"})
EXPECTED_GROUP_COUNT = 39
PROFILE_FILES = {
    "default": "StashKit.yaml",
    "privacy": "StashKit-Privacy.yaml",
    "local": "StashKit-Local.yaml",
}


def read_node_sources(path):
    """Read node entries and provider definitions without modifying user input."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
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
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
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
        try:
            parts = urlsplit(url)
            valid = (parts.scheme == "https" and bool(parts.hostname)
                     and parts.port != 0 and not parts.fragment)
        except ValueError:
            valid = False
        if not valid or "example.invalid" in url or "REPLACE-" in url:
            raise ValueError("Subscription URLs must be real HTTPS links without fragments")
    return urls


def build_loon_selection(source, providers=None, nodes=None, subscription_urls=None):
    """Render standalone groups with both explicit strategies and discovered nodes."""
    providers = copy.deepcopy(providers or {})
    nodes = copy.deepcopy(nodes or [])
    subscription_urls = list(subscription_urls or [])
    if not providers and not nodes and not subscription_urls:
        raise ValueError("Named nodes or providers or subscription URLs are required")
    if subscription_urls and (providers or nodes):
        raise ValueError("Subscription URLs cannot be mixed with inline nodes or named providers")
    if len(subscription_urls) != len(set(subscription_urls)):
        raise ValueError("Duplicate subscription URLs")
    output = copy.deepcopy(source)
    groups = output["proxy-groups"]
    # Private profiles explicitly enumerate nodes/providers and need no helper pool.
    manual = [group for group in groups if group["name"] == "Manual"]
    if manual:
        if (len(manual) != 1 or not manual[0].get("hidden")
                or not manual[0].get("include-all")):
            raise ValueError("Unexpected manual node pool structure")
        groups[:] = [group for group in groups if group["name"] != "Manual"]
    names = [group["name"] for group in groups]
    if (len(groups) != EXPECTED_GROUP_COUNT or len(set(names)) != len(groups)
            or not NODE_POOLS.issubset(names) or "ALL" in names):
        raise ValueError("Unexpected canonical group structure")
    if source.get("proxy-providers") or source.get("proxies"):
        raise ValueError("Canonical profile must not bundle personal nodes/providers")
    local_names = [node["name"] for node in nodes]
    if len(local_names) != len(set(local_names)):
        raise ValueError("Duplicate node names")
    if set(local_names) & (set(names) | {"DIRECT", "REJECT", "REJECT-DROP"}):
        raise ValueError("Node names conflict with strategy group names")
    if set(providers) & set(names):
        raise ValueError("Provider names conflict with strategy group names")

    for group in groups:
        name = group["name"]
        if group["type"] not in {"select", "url-test", "fallback"}:
            raise ValueError(f"Unexpected group type: {name}")
        group.pop("include-all", None)
        group.pop("filter", None)
        if name == "Proxy":
            group["proxies"] = ["REJECT", "Auto", "Fallback"] + local_names
        elif name in {"Auto", "Fallback"}:
            # Keep REJECT if all nodes/providers disappear; otherwise prefer real nodes.
            group["proxies"] = local_names + ["REJECT"]
        elif name not in SERVICE_EXCEPTIONS:
            group["proxies"].extend(local_names)
        if name not in SERVICE_EXCEPTIONS and providers:
            group["use"] = list(providers)
        else:
            group.pop("use", None)
        if name not in SERVICE_EXCEPTIONS and subscription_urls:
            group["use-url"] = subscription_urls
        else:
            group.pop("use-url", None)
    if nodes:
        output["proxies"] = nodes
    if providers:
        output["proxy-providers"] = providers
    validate_profile(output)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=PROFILE_FILES, default="default")
    origin = parser.add_mutually_exclusive_group(required=True)
    origin.add_argument("--nodes-from", type=Path,
                        help="Existing local Clash/Stash YAML: auto-discovers proxy names and providers")
    origin.add_argument("--provider-override", type=Path,
                        help="Legacy local override with proxy-providers definitions")
    origin.add_argument("--subscription-file", type=Path,
                        help="Local text file with HTTPS node subscription URLs, one per line")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    urls = []
    if args.nodes_from:
        nodes, providers = read_node_sources(args.nodes_from)
    elif args.subscription_file:
        nodes, providers = [], {}
        urls = read_subscription_urls(args.subscription_file)
    else:
        nodes, providers = [], read_provider_override(args.provider_override)
    source = yaml.safe_load((ROOT / PROFILE_FILES[args.profile]).read_text(encoding="utf-8"))
    output = build_loon_selection(source, providers, nodes, urls)
    output_file = args.output.resolve()
    if ROOT in output_file.parents and ROOT / "dist" not in output_file.parents:
        raise ValueError("Write private profiles only under dist/ or outside the repository")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(yaml.safe_dump(output, sort_keys=False, allow_unicode=True),
                           encoding="utf-8")
    print(f"Generated private profile from {len(nodes)} local nodes, "
          f"{len(providers)} providers and {len(urls)} direct subscription URL(s): "
          f"{output_file}")


if __name__ == "__main__":
    main()
