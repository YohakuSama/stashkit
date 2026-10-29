#!/usr/bin/env python3
"""Check that all StashKit remote rules actually download from the published GitHub Raw URLs.

By default it checks production immutable URLs. --ref checks candidate bytes at a
commit before merging, without changing production URLs in StashKit.yaml.
"""
import concurrent.futures
import argparse
import hashlib
import sys
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

import yaml

from release_meta import RULES_REF, RULES_URL_PREFIX

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "StashKit.yaml"
PREFIX = RULES_URL_PREFIX


def published_url(spec, ref=None):
    url = spec["url"]
    if not url.startswith(PREFIX):
        raise ValueError(f"Unexpected host/path: {url}")
    basename = url[len(PREFIX):]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*\.txt", basename):
        raise ValueError(f"Unsafe asset URL: {url}")
    if ref is not None:
        if not re.fullmatch(r"[0-9a-f]{40}", ref):
            raise ValueError("--ref must be a full lowercase commit SHA")
        url = PREFIX.replace(f"/{RULES_REF}/rules/", f"/{ref}/rules/") + basename
    return url, basename


def check(item, ref=None):
    name, spec = item
    url, basename = published_url(spec, ref)
    local_path = ROOT / "rules" / basename
    expected = local_path.read_bytes()
    last_error = None
    for attempt in range(1, 4):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "StashKit-publish-validator/1.0",
                         "Accept": "text/plain,*/*"},
            )
            with urllib.request.urlopen(req, timeout=35) as response:
                if response.status != 200:
                    raise AssertionError(f"HTTP {response.status}: {url}")
                downloaded = response.read()
            if downloaded != expected:
                raise AssertionError(
                    f"{name}: HTTP 200 but content SHA mismatch: "
                    f"local={hashlib.sha256(expected).hexdigest()} "
                    f"remote={hashlib.sha256(downloaded).hexdigest()}"
                )
            return name, len(downloaded)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            last_error = error
            if attempt < 3:
                time.sleep(attempt * 2)
    raise AssertionError(f"{name}: unavailable after 3 attempts: {last_error}")


def main(ref=None):
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    items = [(name, spec) for name, spec in config["rule-providers"].items() if "url" in spec]
    if len(items) != 54:
        raise AssertionError(f"Expected 54 providers, got {len(items)}")
    total_bytes = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(check, item, ref): item[0] for item in items}
        for future in concurrent.futures.as_completed(futures):
            name, size = future.result()
            total_bytes += size
            print(f"PASS: {name} HTTP 200, {size} bytes, exact byte-for-byte match")
    print(f"PASS: all 54 pinned GitHub Raw URLs verified at {ref or RULES_REF}, {total_bytes:,} total bytes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", help="full candidate commit SHA; defaults to immutable production snapshot")
    args = parser.parse_args()
    try:
        main(args.ref)
    except Exception as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise
