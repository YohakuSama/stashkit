#!/usr/bin/env python3
"""Build a private Stash profile with LoonKit-style node and policy selection.

Stash include-all can display only node candidates on some clients. Instead,
attach named proxy providers using 'use' while keeping explicit policy options.
Provider definitions and subscription URLs stay in a local, ignored input file.
"""
import argparse
import copy
import sys
from pathlib import Path

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


def read_provider_override(path):
    override = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(override, dict) or set(override) - {"name", "desc", "proxy-providers"}:
        raise ValueError("Expected an override containing only proxy-providers and optional metadata")
    providers = override.get("proxy-providers")
    if not isinstance(providers, dict) or not providers:
        raise ValueError("At least one named proxy provider is required")
    for name, spec in providers.items():
        if not isinstance(name, str) or not name.strip() or not isinstance(spec, dict):
            raise ValueError("Invalid named proxy provider")
        url = spec.get("url", "")
        if not isinstance(url, str) or "example.invalid" in url or "REPLACE-" in url:
            raise ValueError("Replace the example provider with a real subscription URL")
    return providers


def build_loon_selection(source, providers):
    """Generate a standalone profile that mixes named strategies with provider nodes."""
    if not isinstance(providers, dict) or not providers:
        raise ValueError("Named providers are required; include-all alone is insufficient")
    output = copy.deepcopy(source)
    groups = output["proxy-groups"]
    names = [group["name"] for group in groups]
    if (len(groups) != EXPECTED_GROUP_COUNT or len(set(names)) != len(groups)
            or not NODE_POOLS.issubset(names) or "ALL" in names):
        raise ValueError("Unexpected canonical group structure")
    if source.get("proxy-providers"):
        raise ValueError("Provider definitions must come from the private override")
    if set(providers) & set(names):
        raise ValueError("Provider names must not conflict with strategy group names")

    for group in groups:
        name = group["name"]
        if group["type"] not in {"select", "url-test", "fallback"}:
            raise ValueError(f"Unexpected group type: {name}")
        group.pop("include-all", None)
        if name == "Proxy":
            group["proxies"] = ["REJECT", "Auto", "Fallback"]
        elif name in {"Auto", "Fallback"}:
            group["proxies"] = ["REJECT"]
        if name not in SERVICE_EXCEPTIONS:
            group["use"] = list(providers)
        else:
            group.pop("use", None)

    output["proxy-providers"] = copy.deepcopy(providers)
    validate_profile(output)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=PROFILE_FILES, default="default")
    parser.add_argument("--provider-override", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    providers = read_provider_override(args.provider_override)
    source = yaml.safe_load((ROOT / PROFILE_FILES[args.profile]).read_text(encoding="utf-8"))
    output = build_loon_selection(source, providers)
    output_file = args.output.resolve()
    if ROOT in output_file.parents and ROOT / "dist" not in output_file.parents:
        raise ValueError("Write private profiles only under dist/ or outside the repository")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(yaml.safe_dump(output, sort_keys=False, allow_unicode=True),
                           encoding="utf-8")
    print(f"PASS: generated private Stash profile with {len(providers)} named provider(s): "
          f"{output_file.name}")


if __name__ == "__main__":
    main()
