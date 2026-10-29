#!/usr/bin/env python3
"""Verify all 39 pinned, self-hosted Stash strategy icons via real HTTPS downloads."""
import concurrent.futures
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check_icon(item, prefix):
    filename, git_sha = item
    local = (ROOT / "icons" / filename).read_bytes()
    assert local.startswith(bytes.fromhex("89504e470d0a1a0a")), filename
    assert hashlib.sha1(b"blob " + str(len(local)).encode() + bytes([0]) + local).hexdigest() == git_sha, filename
    url = prefix + filename
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "StashKit-icon-audit/1.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status != 200:
                    raise ValueError(f"{filename}: HTTP {response.status}")
                remote = response.read()
            if remote != local:
                raise AssertionError(f"{filename}: remote bytes differ from the committed PNG")
            return filename, len(remote)
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def main():
    lock = json.loads((ROOT / "build/icon-lock.json").read_text(encoding="utf-8"))
    ref = lock["icons_commit"]
    prefix = f"https://raw.githubusercontent.com/YohakuSama/stashkit/{ref}/icons/"
    items = sorted(lock["asset_git_blob_shas"].items())
    assert len(items) == 39
    count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(check_icon, item, prefix) for item in items]
        for future in concurrent.futures.as_completed(futures):
            name, size = future.result()
            count += 1
            print(f"PASS: {name}, HTTP 200, {size:,} bytes, exact match")
    assert count == 39
    print("PASS: all 39 original StashKit icon URLs are reachable and unchanged")


if __name__ == "__main__":
    main()
