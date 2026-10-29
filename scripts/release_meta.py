#!/usr/bin/env python3
"""Validate and expose the profile version and immutable rule snapshot lock."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "build/release-lock.json"
VERSION_PATTERN = re.compile(r"v[0-9]+\.[0-9]+\.[0-9]+\Z")
REF_PATTERN = re.compile(r"[0-9a-f]{40}\Z")


def load_lock(path=LOCK_PATH):
    data = json.loads(path.read_text(encoding="utf-8"))
    if set(data) != {"profile_version", "rules_version", "source_ref"}:
        raise ValueError("Unexpected release lock fields")
    if any(not isinstance(data[k], str) or not VERSION_PATTERN.fullmatch(data[k])
           for k in ("profile_version", "rules_version")):
        raise ValueError("Invalid profile or rules version")
    if not isinstance(data["source_ref"], str) or not REF_PATTERN.fullmatch(data["source_ref"]):
        raise ValueError("Invalid immutable rule snapshot ref")
    return data


LOCK = load_lock()
PROFILE_VERSION = LOCK["profile_version"]
RULES_VERSION = LOCK["rules_version"]
RULES_REF = LOCK["source_ref"]
RULES_PATH_PREFIX = f"./rules/{RULES_VERSION}/"
RULES_URL_PREFIX = f"https://raw.githubusercontent.com/YohakuSama/stashkit/{RULES_REF}/rules/"


def archive_name():
    return f"StashKit-{PROFILE_VERSION}-offline.zip"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    options = parser.add_mutually_exclusive_group(required=True)
    options.add_argument("--profile-version", action="store_true")
    options.add_argument("--archive-name", action="store_true")
    options.add_argument("--rules-version", action="store_true")
    args = parser.parse_args()
    if args.profile_version:
        print(PROFILE_VERSION)
    elif args.archive_name:
        print(archive_name())
    else:
        print(RULES_VERSION)


if __name__ == "__main__":
    main()
