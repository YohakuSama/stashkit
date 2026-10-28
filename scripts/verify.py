#!/usr/bin/env python3
"""StashKit static compatibility checks against the LoonKit production baseline."""
import hashlib
import ipaddress
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml
from validate_config import validate_profile, validate_override

KIT = Path(__file__).resolve().parents[1]
ROOT = KIT / "upstream" / "loonkit"
SOURCE_URL = "https://raw.githubusercontent.com/YohakuSama/stashkit/main/rules/"
SUPPORTED = {"DOMAIN", "DOMAIN-SUFFIX", "IP-CIDR", "IP-CIDR6", "IP-ASN"}
LOCAL_DIRECT_RULES = [
    "DOMAIN,localhost,DIRECT",
    "DOMAIN-SUFFIX,local,DIRECT",
    "DOMAIN-SUFFIX,lan,DIRECT",
    "DOMAIN-SUFFIX,home.arpa,DIRECT",
    "GEOSITE,private,DIRECT",
    "GEOIP,LAN,DIRECT,no-resolve",
]


class UniqueKeysLoader(yaml.SafeLoader):
    pass


def construct_mapping(loader, node):
    output = {}
    for key, value in node.value:
        k = loader.construct_object(key, deep=True)
        if k in output:
            raise AssertionError(f"Duplicate YAML key: {k}")
        output[k] = loader.construct_object(value, deep=True)
    return output


UniqueKeysLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)


def valid_domain(value):
    assert value and not value.startswith(".") and not value.endswith("."), value
    assert not any(x in value for x in (" ", "/", ",", "*", "+")), value
    # Not a DNS validity oracle; protects against accidentally passing a Clash rule token.
    assert len(value) <= 253, value


def lines_from(path):
    return [row.strip() for row in path.read_text(encoding="utf-8").splitlines()
            if row.strip() and not row.lstrip().startswith("#")]


def generate_source_sets(path):
    buckets = {"domain": [], "ipcidr": [], "asn": []}
    raw = lines_from(path)
    assert len(raw) == len(set(raw)), f"Duplicated LoonKit source entries: {path}"
    for row in raw:
        pieces = row.split(",")
        assert len(pieces) >= 2 and pieces[0] in SUPPORTED, (path, row)
        kind, value = pieces[:2]
        opts = pieces[2:]
        if kind in ("DOMAIN", "DOMAIN-SUFFIX"):
            assert not opts, (path, row)
            valid_domain(value)
            buckets["domain"].append(value if kind == "DOMAIN" else "+." + value)
        elif kind in ("IP-CIDR", "IP-CIDR6"):
            assert opts == ["no-resolve"], (path, row)
            network = ipaddress.ip_network(value, strict=False)
            assert network.version == (4 if kind == "IP-CIDR" else 6), (path, row)
            buckets["ipcidr"].append(value)
        else:
            assert opts == ["no-resolve"] and value.isdigit(), (path, row)
            buckets["asn"].append(row)
    return buckets, len(raw)


def load_adjustments():
    data = json.loads((KIT / "build/adjustments.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert data["source_commit"] == "5f272104fc1207612c1cbd18f3e19d861d459ed9"
    assert len({(c["source"], c["behavior"]) for c in data["changes"]}) == len(data["changes"])
    return data


def apply_adjustments(base, buckets, adjustments):
    """Apply only explicit, reviewed changes after validating the upstream input."""
    for change in adjustments["changes"]:
        if change["source"] != base:
            continue
        assert change["behavior"] == "domain", change
        assert change["reason"].strip(), change
        values = buckets["domain"]
        for value in change["remove"]:
            assert value in values, (base, "missing removal", value)
            values.remove(value)
        for value in change["add"]:
            valid_domain(value[2:] if value.startswith("+.") else value)
            assert value not in values, (base, "duplicate addition", value)
            values.append(value)
    return buckets


def main():
    assert ROOT.is_dir(), "Missing pinned upstream/loonkit checkout"
    manifest = json.loads((ROOT / "build/release_manifest.json").read_text(encoding="utf-8"))
    profile = yaml.load((KIT / "StashKit.yaml").read_text(encoding="utf-8"), Loader=UniqueKeysLoader)
    validate_profile(profile)
    example = yaml.load((KIT / "overrides/provider.stoverride.example").read_text(encoding="utf-8"), Loader=UniqueKeysLoader)
    validate_override(example)
    original = (ROOT / "LoonKit.lcf").read_text(encoding="utf-8")
    resources = manifest["runtime_resources"]
    adjustments = load_adjustments()
    assert {c["source"] for c in adjustments["changes"]} <= {Path(r["path"]).stem for r in resources}
    assert manifest["label"] == "v7.0.10", "Regenerate StashKit when LoonKit baseline updates"
    assert len(resources) == manifest["remote_subscription_count"] == 43
    assert profile["mode"] == "rule"
    dns = profile["dns"]
    assert dns["nameserver"] == ["https://dns.alidns.com/dns-query"]
    assert dns["default-nameserver"] == ["https://223.5.5.5/dns-query"]
    assert dns["proxy-server-nameserver"] == ["https://223.5.5.5/dns-query"]
    assert dns["follow-rule"] is False
    assert dns["fake-ip-range"] == "198.18.0.1/16"
    # No LoonKit 'real-ip' blanket exemptions: protected domains should use
    # Fake-IP unless an explicit Stash compatibility case requires otherwise.
    filters = set(dns["fake-ip-filter"])
    assert "geosite:private" in filters
    assert "+.apple.com" not in filters and "+.icloud.com" not in filters
    assert "captive.apple.com" in filters
    assert all(not entry.startswith(("http://", "udp://", "tcp://")) and
               (entry.startswith("https://") or entry == "system")
               for entry in dns["default-nameserver"] + dns["nameserver"] + dns["proxy-server-nameserver"])
    assert not (set(profile) & {"hijack-dns", "real-ip", "skip-proxy", "bypass-tun",
                                  "disable-stun", "dns-reject-mode", "domain-reject-mode",
                                  "udp-fallback-mode", "interface-mode"}), "Unsupported Loon-only directives"
    source_groups = original.split("[Proxy Group]", 1)[1].split("[Remote Rule]", 1)[0]
    group_names = [row.split("=", 1)[0].strip() for row in source_groups.splitlines() if " = " in row]
    groups = profile["proxy-groups"]
    names = [group["name"] for group in groups]
    assert len(group_names) == 39 and len(names) == len(set(names)) == 40
    assert names == group_names[:3] + ["ALL"] + group_names[3:], "Group order changed"
    by_name = {group["name"]: group for group in groups}
    assert by_name["Auto"]["type"] == "url-test" and by_name["Auto"]["interval"] == 600
    assert by_name["Auto"]["tolerance"] == 60
    assert by_name["Fallback"]["type"] == "fallback" and by_name["Fallback"]["interval"] == 900
    assert by_name["ALL"]["type"] == "select"
    for group in (by_name["Auto"], by_name["Fallback"], by_name["ALL"]):
        assert group["include-all"] and group["proxies"] == ["REJECT"], "Missing unconfigured-pool REJECT placeholder"
    assert by_name["AdBlock"]["proxies"][0] == "REJECT"
    assert by_name["Final"]["proxies"][0] == "Proxy"
    assert by_name["Microsoft"]["proxies"][0] == "DIRECT"
    for group in groups:
        for child in group["proxies"]:
            assert child in names or child in ("DIRECT", "REJECT"), (group["name"], child)
        if group.get("icon"):
            assert group["icon"].startswith("https://raw.githubusercontent.com/YohakuSama/loonkit/")
    expected_providers = {}
    expected_routes = []
    total = 0
    domain_count = ip_count = asn_count = 0
    for src in resources:
        original_path = ROOT / src["path"]
        assert original_path.is_file(), src["path"]
        original_bytes = original_path.read_bytes()
        assert hashlib.sha256(original_bytes).hexdigest() == src["sha256"], f"SHA mismatch: {src['path']}"
        buckets, count = generate_source_sets(original_path)
        assert count == src["matcher_count"], f"Source count mismatch: {src['path']}"
        total += count
        base = original_path.stem
        apply_adjustments(base, buckets, adjustments)
        assert src["policy"] == "DIRECT" or src["policy"] in names, src["policy"]
        for behavior in ("domain", "ipcidr", "asn"):
            values = buckets[behavior]
            if not values:
                continue
            path = KIT / "rules" / f"{base}.{behavior}.txt"
            assert path.is_file(), path
            saved = lines_from(path)
            assert saved == values, f"Source parity failed: {path}"
            assert len(saved) == len(set(saved)), f"Generated duplicates: {path}"
            if behavior == "domain":
                for item in saved:
                    valid_domain(item[2:] if item.startswith("+.") else item)
                domain_count += len(saved)
            elif behavior == "ipcidr":
                for item in saved:
                    ipaddress.ip_network(item, strict=False)
                ip_count += len(saved)
            else:
                assert all(re.fullmatch(r"IP-ASN,\d+,no-resolve", item) for item in saved)
                asn_count += len(saved)
            key = f"{base}-{behavior}"
            expected_providers[key] = {
                "behavior": "classical" if behavior == "asn" else behavior,
                "format": "text",
                "url": SOURCE_URL + path.name,
                "interval": 86400,
            }
            expected_routes.append("RULE-SET," + key + "," + src["policy"] + (
                ",no-resolve" if behavior == "ipcidr" else ""))
    assert total == manifest["remote_rule_count"] == 196561, total
    generated_total = domain_count + ip_count + asn_count
    assert generated_total == adjustments["expected_generated_rule_count"], generated_total
    assert profile["rule-providers"] == expected_providers, "Provider names/URL/types are inconsistent"
    assert len(expected_providers) == 54
    assert len(list((KIT / "rules").glob("*.txt"))) == 54
    source_rule_section = original.split("[Rule]", 1)[1].split("[Plugin]", 1)[0]
    source_rules = [row.strip() for row in source_rule_section.splitlines() if row.strip()]
    assert source_rules[0] == "DOMAIN-SUFFIX,raw.githubusercontent.com,Proxy"
    source_rules[0] = "DOMAIN-SUFFIX,raw.githubusercontent.com,GitHub"
    expected_rules = LOCAL_DIRECT_RULES + source_rules[:-2] + expected_routes + ["GEOIP,CN,DIRECT,no-resolve", "MATCH,Final"]
    assert profile["rules"] == expected_rules, "Rules changed order, policy, or local precedence"
    assert profile["rules"][-1] == "MATCH,Final"
    assert len(expected_routes) == 54
    print(f"PASS: {len(resources)} production LoonKit sources; {len(expected_providers)} Stash "
          f"rule providers; {len(names)} groups; {generated_total:,} rules "
          f"({domain_count:,} domain / {ip_count:,} CIDR / {asn_count:,} ASN).")
    print("PASS: SHA-256, reviewed source adjustments, no within-set duplicates, project schema, "
          "acyclic group references, no-resolve, provider URLs and expected routing order.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise
