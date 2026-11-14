#!/usr/bin/env python3
"""Build compatibility profiles and an on-demand offline profile from StashKit.yaml."""
import argparse
import re
from pathlib import Path

import yaml

from build_loon_selection import build_loon_selection
from release_meta import PROFILE_VERSION, RULES_PATH_PREFIX

ROOT = Path(__file__).resolve().parents[1]
HEADER = f"# StashKit {PROFILE_VERSION}\n"
LOCAL_HEADER = f"# StashKit {PROFILE_VERSION} — local rule providers\n"
SUBSCRIPTION_BLOCK = (
    "# Edit the subscription URL locally; never publish private subscription credentials.\n"
    "proxy-providers:\n"
    "  Airport:\n"
    "    # Replace this URL with your private Clash/Stash YAML subscription.\n"
    "    url: 'https://example.invalid/REPLACE-WITH-YOUR-CLASH-SUBSCRIPTION'\n"
    "    path: ./providers/stashkit-airport.yaml\n"
    "    interval: 3600\n"
)
REMOTE_PROVIDER_LINE = re.compile(
    r'^(  "[^"]+": \{behavior: (?:domain|ipcidr|classical), format: text), '
    r'url: https://raw\.githubusercontent\.com/YohakuSama/stashkit/'
    r'[0-9a-f]{40}/rules/(?:extra/)?[A-Za-z0-9_.-]+\.txt, '
    r'path: (\./rules/[A-Za-z0-9_./-]+\.txt), interval: 86400\}\n',
    re.M,
)


def replace_once(content, old, new, context):
    if content.count(old) != 1:
        raise ValueError(f"{context}: expected exactly one source occurrence")
    return content.replace(old, new, 1)


def local_profile(config=None):
    content = config if config is not None else (ROOT / "StashKit.yaml").read_text(encoding="utf-8")
    content = replace_once(content, HEADER, LOCAL_HEADER, "profile header")
    parts = content.split("\nrule-providers:\n")
    if len(parts) != 2:
        raise ValueError("Expected one rule-providers section")
    sections = parts[1].split("\nrules:\n")
    if len(sections) != 2:
        raise ValueError("Expected one rules section after rule-providers")
    providers, count = REMOTE_PROVIDER_LINE.subn(r'\1, path: \2}' + "\n", sections[0])
    if count != 55:
        raise ValueError("Expected 54 frozen remote providers plus 1 pinned Crypto provider")
    return parts[0] + "\nrule-providers:\n" + providers + "\nrules:\n" + sections[1]



def subscription_profile(config=None):
    """Keep the old Subscription filename as an alias of the official main profile."""
    content = config if config is not None else (ROOT / "StashKit.yaml").read_text(encoding="utf-8")
    if content.count("    use:\n      - Airport\n") != 38 or content.count("proxy-providers:\n") != 1:
        raise ValueError("Expected 38 policy groups bound to the official Airport provider")
    return content


def derived_profiles(config):
    outputs = {"StashKit-Subscription.yaml": subscription_profile(config)}
    # ALL remains an explicit compatibility variant, never a default alias.
    for filename, content in (("StashKit-ALL.yaml", config),):
        legacy = build_loon_selection(yaml.safe_load(content),
                                      providers={"binding": {"path": "./unused.yaml"}},
                                      layout="nested")
        legacy.pop("proxy-providers")
        for group in legacy["proxy-groups"]:
            group.pop("use", None)
            if group["name"] in {"Auto", "Fallback", "ALL"}:
                group.update({"include-all": True, "filter": ".*"})
        outputs[filename] = (content.splitlines()[0] + " — legacy ALL compatibility\n"
                             + yaml.safe_dump(legacy, sort_keys=False, allow_unicode=True))
    source = yaml.safe_load(config)
    for filename, layout in (("StashKit-Loon-Preview.yaml", "nested"),
                             ("StashKit-Native-Preview.yaml", "native")):
        preview = build_loon_selection(source,
                                       providers={"personal": {"path": "./providers/personal.yaml"}},
                                       layout=layout)
        preview.pop("proxy-providers")
        outputs[filename] = (f"# StashKit {PROFILE_VERSION} — provider reference only\n"
                             "# Define a real personal provider before importing this reference.\n"
                             + yaml.safe_dump(preview, sort_keys=False, allow_unicode=True))
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    source = (ROOT / "StashKit.yaml").read_text(encoding="utf-8")
    outputs = derived_profiles(source)
    if args.check:
        mismatches = [name for name, value in outputs.items()
                      if (ROOT / name).read_bytes() != value.encode("utf-8")]
        if mismatches:
            raise ValueError(f"Derived profiles differ from canonical source: {mismatches}")
        print("PASS: 40-group subscription and compatibility variants match canonical source")
    else:
        for name, value in outputs.items():
            (ROOT / name).write_text(value, encoding="utf-8")
        print("Updated derived profiles and explicit compatibility variants from StashKit.yaml")


if __name__ == "__main__":
    main()
