#!/usr/bin/env python3
"""Read-only Stash HTTP API smoke test for a real iOS/macOS device.

Must run on a trusted host able to reach the Stash external controller.
Never prints your secret, subscriptions or raw DNS history.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def get_json(base, token, resource, opener=None):
    if opener is None:
        opener = urllib.request.urlopen
    req = urllib.request.Request(
        base.rstrip("/") + resource,
        headers={"Authorization": "Bearer " + token,
                 "Accept": "application/json",
                 "User-Agent": "StashKit-runtime-audit"},
    )
    with opener(req, timeout=12) as response:
        if response.status != 200:
            raise ValueError("Stash controller responded with HTTP " + str(response.status))
        return json.load(response)


def inspect(base, token, getter=get_json):
    failures = []
    version = getter(base, token, "/version")
    print("PASS: authenticated connection to Stash runtime")
    print("INFO: version fields:", sorted(version) if isinstance(version, dict) else "<not a mapping>")
    config = getter(base, token, "/configs")
    if config.get("mode") != "rule":
        failures.append("Stash is not in rule mode")
    print("INFO: configured mode:", config.get("mode"))
    groups = getter(base, token, "/proxies")
    proxies = groups.get("proxies", groups) if isinstance(groups, dict) else {}
    current = proxies.get("Proxy", {}).get("now") if isinstance(proxies, dict) else None
    print("INFO: Proxy selection:", current or "unavailable from controller")
    if current in (None, "DIRECT"):
        failures.append("Cannot confirm a safe Proxy selection")
    if current == "REJECT":
        print("INFO: fail-closed default active; enable a real node before testing services")
    providers = getter(base, token, "/providers/rules")
    objects = providers.get("providers", providers) if isinstance(providers, dict) else {}
    count = len(objects) if isinstance(objects, (dict, list)) else None
    print("INFO: Stash reported rule-provider count:", count)
    if count != 54:
        failures.append(f"Expected 54 loaded rule providers, controller showed {count}")
    count_result = getter(base, token, "/rules/count")
    print("INFO: live rule count response keys:",
          sorted(count_result) if isinstance(count_result, dict) else "<unknown>")
    for target in ("192.168.1.1", "api.openai.com", "raw.githubusercontent.com",
                   "control.kochava.com", "alibaba.cdn.steampipe.steamcontent.com"):
        query = urllib.parse.urlencode({"target": target, "resolve": "false"})
        decision = getter(base, token, "/rules/match?" + query)
        # Only display safe non-secret routing diagnostics.
        safe = {k: v for k, v in decision.items() if k in
                {"outbound", "proxy", "proxyChain", "ruleType", "rulePayload", "type", "policy"}}
        print(f"INFO: {target} -> {json.dumps(safe, ensure_ascii=False)[:250]}")
    mem = getter(base, token, "/diagnosis/usedMemory")
    print("INFO: memory metric fields:", sorted(mem) if isinstance(mem, dict) else "<unknown>")
    if failures:
        for failure in failures:
            print("WARN:", failure, file=sys.stderr)
        return False
    print("PASS: controller rule mode and 54 provider presence; routing needs manual inspection")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:9090",
                        help="Stash HTTP controller; use only trusted LAN or loopback")
    args = parser.parse_args()
    parsed = urllib.parse.urlsplit(args.base_url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        parser.error("Expected a Stash HTTP(S) controller URL")
    token = os.environ.get("STASH_API_TOKEN")
    if not token:
        parser.error("Set STASH_API_TOKEN in your environment; never put it in the URL")
    try:
        if not inspect(args.base_url, token):
            raise SystemExit(1)
    except (urllib.error.URLError, ValueError, KeyError, TypeError) as error:
        print("FAIL: runtime API check failed:", type(error).__name__, file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
