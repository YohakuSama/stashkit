#!/usr/bin/env python3
"""Read-only Stash acceptance checks for the selected shipped profile.

Checks configuration and routing decisions, not actual service connectivity.
Never prints credentials, private node names, subscriptions or DNS history.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
BUILTINS = {"DIRECT", "REJECT", "REJECT-DROP"}
SENTINELS = (
    ("192.168.1.1", "GEOIP", "LAN", "DIRECT"),
    ("router.internal", "RULE-SET", "Private-local", "DIRECT"),
    ("api.openai.com", "RULE-SET", "ChatGPT-domain", "ChatGPT"),
    ("raw.githubusercontent.com", "DOMAIN-SUFFIX", "raw.githubusercontent.com", "GitHub"),
    ("control.kochava.com", "RULE-SET", "AdBlockBalanced-domain", "AdBlock"),
    ("googleads.g.doubleclick.net", "RULE-SET", "AdBlockBalanced-domain", "AdBlock"),
    ("pagead2.googlesyndication.com", "RULE-SET", "AdBlockBalanced-domain", "AdBlock"),
    ("www.googleadservices.com", "RULE-SET", "AdBlockBalanced-domain", "AdBlock"),
    ("www.google-analytics.com", "RULE-SET", "AdBlockBalanced-domain", "AdBlock"),
    ("copilot-telemetry.githubusercontent.com", "RULE-SET", "AdBlockBalanced-domain", "AdBlock"),
    ("alibaba.cdn.steampipe.steamcontent.com", "RULE-SET", "SteamCN-domain", "DIRECT"),
)


def get_json(base, token, resource, opener=None):
    if opener is None:
        opener = urllib.request.urlopen
    req = urllib.request.Request(
        base.rstrip("/") + resource,
        headers={"Authorization": "Bearer " + token, "Accept": "application/json",
                 "User-Agent": "StashKit-runtime-audit"},
    )
    with opener(req, timeout=12) as response:
        if response.status != 200:
            raise ValueError("Stash controller did not return HTTP 200")
        return json.load(response)


def named_objects(response, key):
    value = response.get(key, response) if isinstance(response, dict) else response
    if isinstance(value, dict) and all(isinstance(v, dict) for v in value.values()):
        return value
    if isinstance(value, list) and all(isinstance(v, dict) and isinstance(v.get("name"), str) for v in value):
        objects = {v["name"]: v for v in value}
        if len(objects) == len(value):
            return objects
    raise ValueError("Controller returned an unsupported object collection")


def resolve_policy(name, proxies):
    visited = set()
    while name not in BUILTINS:
        if name in visited or name not in proxies:
            raise ValueError("Policy has a cycle or an unknown selection")
        visited.add(name)
        spec = proxies[name]
        kind = str(spec.get("type", "")).lower().replace("-", "")
        if kind in {"direct", "reject", "rejectdrop"}:
            return {"direct": "DIRECT", "reject": "REJECT", "rejectdrop": "REJECT-DROP"}[kind]
        if "now" in spec:
            if not isinstance(spec["now"], str) or not spec["now"]:
                raise ValueError("Policy selection is missing")
            name = spec["now"]
        elif "all" in spec or kind in {"selector", "select", "urltest", "fallback", "loadbalance", "relay"}:
            raise ValueError("Policy group has no verifiable current selection")
        elif kind:
            return name
        else:
            raise ValueError("Selected node has no verifiable type")
    return name


def expected_counts(profile, root=ROOT):
    counts = {}
    for name, spec in profile["rule-providers"].items():
        if spec.get("type") == "inline":
            counts[name] = len(spec["payload"])
        else:
            filename = spec.get("url", spec.get("path", "")).rsplit("/", 1)[-1]
            counts[name] = sum(bool(row.strip()) and not row.lstrip().startswith("#")
                               for row in (root / "rules" / filename).read_text().splitlines())
    return counts


def rule_identity(decision):
    rule = decision.get("rule", {})
    if isinstance(rule, dict):
        kind = rule.get("type", rule.get("ruleType"))
        payload = rule.get("payload", rule.get("rulePayload"))
    else:
        kind = payload = None
    kind = decision.get("ruleType", kind)
    payload = decision.get("rulePayload", payload)
    return re.sub(r"[^a-z]", "", str(kind).lower()), payload


def inspect(base, token, getter=get_json, profile=None):
    profile = profile if profile is not None else yaml.safe_load((ROOT / "StashKit.yaml").read_text())
    failures = []
    getter(base, token, "/version")
    print("PASS: authenticated connection to Stash runtime")
    config = getter(base, token, "/configs")
    if not isinstance(config, dict) or config.get("mode") != "rule":
        failures.append("Stash is not in rule mode")
    proxies = named_objects(getter(base, token, "/proxies"), "proxies")
    try:
        if resolve_policy("Proxy", proxies) in BUILTINS:
            failures.append("Proxy must resolve to a configured node before service acceptance")
    except ValueError as error:
        failures.append(str(error))
    providers = named_objects(getter(base, token, "/providers/rules"), "providers")
    counts = expected_counts(profile)
    for name, expected in counts.items():
        spec = providers.get(name)
        if not isinstance(spec, dict):
            failures.append(f"Missing rule provider: {name}")
            continue
        count = spec.get("ruleCount", spec.get("count"))
        if type(count) is not int or count != expected:
            failures.append(f"Rule provider has missing or unexpected entry count: {name}")
        if spec.get("error") or spec.get("lastError") or str(spec.get("status", "")).lower() in {"error", "failed", "unloaded"}:
            failures.append(f"Rule provider reports a load failure: {name}")
    minimum = sum(counts[row.split(",")[1]] if row.startswith("RULE-SET,") else 1 for row in profile["rules"])
    count_result = getter(base, token, "/rules/count")
    count = count_result.get("count") if isinstance(count_result, dict) else None
    if type(count) is not int or count < minimum:
        failures.append("Total loaded rule count is missing or below the profile minimum")
    for target, kind, payload, policy in SENTINELS:
        query = urllib.parse.urlencode({"target": target, "resolve": "false"})
        decision = getter(base, token, "/rules/match?" + query)
        try:
            expected = resolve_policy(policy, proxies)
            if policy in {"ChatGPT", "GitHub"} and expected in BUILTINS:
                raise ValueError("Service policy does not resolve to a configured node")
            if not isinstance(decision, dict) or rule_identity(decision) != (re.sub(r"[^a-z]", "", kind.lower()), payload):
                raise ValueError("Unexpected or missing matched rule")
            outbound = decision.get("outbound")
            if isinstance(outbound, dict):
                outbound = outbound.get("name")
            if outbound != expected:
                raise ValueError("Unexpected or missing final outbound")
            print(f"PASS: {target} matches {policy} with the selected outbound")
        except ValueError as error:
            failures.append(f"{target}: {error}")
    getter(base, token, "/diagnosis/usedMemory")
    if failures:
        for failure in failures:
            print("FAIL:", failure, file=sys.stderr)
        return False
    print(f"PASS: {len(counts)} providers, loaded counts, selected node and all routing sentinels verified")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:9090",
                        help="Stash HTTP controller; use only trusted LAN or loopback")
    parser.add_argument("--profile", type=Path, default=ROOT / "StashKit.yaml",
                        help="Shipped profile whose providers and routing should be loaded")
    args = parser.parse_args()
    parsed = urllib.parse.urlsplit(args.base_url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
        parser.error("Expected a Stash HTTP(S) controller URL without embedded credentials")
    token = os.environ.get("STASH_API_TOKEN")
    if not token:
        parser.error("Set STASH_API_TOKEN in your environment; never put it in the URL")
    try:
        profile = yaml.safe_load(args.profile.read_text())
        if not inspect(args.base_url, token, profile=profile):
            raise SystemExit(1)
    except (urllib.error.URLError, ValueError, KeyError, TypeError, OSError, yaml.YAMLError) as error:
        print("FAIL: runtime API check failed:", type(error).__name__, file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
