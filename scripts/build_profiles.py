#!/usr/bin/env python3
"""Build the privacy and offline profiles from the canonical StashKit.yaml."""
import argparse
import re
from pathlib import Path

from release_meta import PROFILE_VERSION, RULES_PATH_PREFIX

ROOT = Path(__file__).resolve().parents[1]
HEADER = f"# StashKit {PROFILE_VERSION}\n"
PRIVACY_HEADER = f"# StashKit {PROFILE_VERSION} — privacy DNS\n"
LOCAL_HEADER = f"# StashKit {PROFILE_VERSION} — local rule providers\n"
PRIVACY_DNS_RULE = '  - "DOMAIN,dns.alidns.com,Proxy"\n'
URL_LINE = re.compile(
    r"^    url: https://raw\.githubusercontent\.com/YohakuSama/stashkit/"
    r"[0-9a-f]{40}/rules/[A-Za-z0-9_.-]+\.txt\n", re.M
)
INTERVAL_LINE = re.compile(r"^    interval: 86400\n", re.M)
LOCAL_PATH = re.compile(r"^    path: " + re.escape(RULES_PATH_PREFIX) + r"[\w.-]+\.txt$", re.M)


def replace_once(content, old, new, context):
    if content.count(old) != 1:
        raise ValueError(f"{context}: expected exactly one source occurrence")
    return content.replace(old, new, 1)


def privacy_profile(config=None):
    content = config if config is not None else (ROOT / "StashKit.yaml").read_text(encoding="utf-8")
    content = replace_once(content, HEADER, PRIVACY_HEADER, "profile header")
    content = replace_once(content, "  follow-rule: false\n", "  follow-rule: true\n", "privacy DNS")
    return replace_once(content, "rules:\n",
                        "rules:\n" + PRIVACY_DNS_RULE, "privacy routing")


def local_profile(config=None):
    content = config if config is not None else (ROOT / "StashKit.yaml").read_text(encoding="utf-8")
    content = replace_once(content, HEADER, LOCAL_HEADER, "profile header")
    parts = content.split("\nrule-providers:\n")
    if len(parts) != 2:
        raise ValueError("Expected one rule-providers section")
    sections = parts[1].split("\nrules:\n")
    if len(sections) != 2:
        raise ValueError("Expected one rules section after rule-providers")
    providers, urls = URL_LINE.subn("", sections[0])
    providers, intervals = INTERVAL_LINE.subn("", providers)
    if (urls, intervals) != (54, 54) or len(LOCAL_PATH.findall(providers)) != 54:
        raise ValueError("Expected 54 pinned remote providers with local cache paths")
    return parts[0] + "\nrule-providers:\n" + providers + "\nrules:\n" + sections[1]


def derived_profiles(config):
    return {
        "StashKit-Privacy.yaml": privacy_profile(config),
        "StashKit-Local.yaml": local_profile(config),
    }


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
        print("PASS: privacy and local profiles match canonical source")
    else:
        for name, value in outputs.items():
            (ROOT / name).write_text(value, encoding="utf-8")
        print("Updated privacy and local profiles from StashKit.yaml")


if __name__ == "__main__":
    main()
