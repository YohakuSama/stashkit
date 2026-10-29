#!/usr/bin/env python3
"""StashKit static compatibility checks against the LoonKit production baseline."""
import hashlib
import json
import ipaddress
import re
import sys
from pathlib import Path

import yaml
from validate_config import validate_profile, validate_override
from rule_sources import (KIT, ROOT, valid_domain, lines_from, generate_source_sets,
                          load_adjustments, apply_adjustments, load_baseline, render_asset)

SOURCE_URL = "https://raw.githubusercontent.com/YohakuSama/stashkit/d63fa06b915d403e2cebc782a8f1551d32b6c927/rules/"
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


def main():
    assert ROOT.is_dir(), "Missing pinned upstream/loonkit checkout"
    manifest, original = load_baseline()
    profile = yaml.load((KIT / "StashKit.yaml").read_text(encoding="utf-8"), Loader=UniqueKeysLoader)
    validate_profile(profile)
    example = yaml.load((KIT / "overrides/provider.stoverride.example").read_text(encoding="utf-8"), Loader=UniqueKeysLoader)
    validate_override(example)
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
    assert by_name["Proxy"]["proxies"] == ["REJECT", "Auto", "Fallback", "ALL"], "Default Proxy must fail closed"
    assert by_name["AdBlock"]["proxies"][0] == "REJECT"
    assert by_name["Final"]["proxies"][0] == "Proxy"
    assert by_name["Microsoft"]["proxies"][0] == "DIRECT"
    icon_lock = json.loads((KIT / "build/icon-lock.json").read_text(encoding="utf-8"))
    icon_ref = icon_lock["icons_commit"]
    assert len(icon_ref) == 40 and all(c in "0123456789abcdef" for c in icon_ref)
    assert set(icon_lock["group_icons"]) == set(names)
    assert len(icon_lock["asset_git_blob_shas"]) == 40
    for filename, expected_sha in icon_lock["asset_git_blob_shas"].items():
        asset_path = KIT / "icons" / filename
        assert asset_path.is_file(), f"Missing self-hosted strategy icon: {filename}"
        blob = asset_path.read_bytes()
        assert blob.startswith(bytes.fromhex("89504e470d0a1a0a")), f"Invalid PNG: {filename}"
        calculated_sha = hashlib.sha1(b"blob " + str(len(blob)).encode("ascii") + bytes([0]) + blob).hexdigest()
        assert calculated_sha == expected_sha, f"Icon changed: {filename}"
    for group in groups:
        for child in group["proxies"]:
            assert child in names or child in ("DIRECT", "REJECT"), (group["name"], child)
        expected_icon = icon_lock["group_icons"][group["name"]]
        assert group["icon"] == (f"https://raw.githubusercontent.com/YohakuSama/stashkit/"
                                 f"{icon_ref}/icons/{expected_icon}"), f"Wrong icon URL: {group['name']}"
        assert expected_icon in icon_lock["asset_git_blob_shas"]
    release_lock = __import__("json").loads((KIT / "build/release-lock.json").read_text(encoding="utf-8"))
    assert release_lock == {"version": "v0.1.3", "source_ref": "d63fa06b915d403e2cebc782a8f1551d32b6c927"}, "Immutable release lock changed"
    assert SOURCE_URL == f"https://raw.githubusercontent.com/YohakuSama/stashkit/{release_lock['source_ref']}/rules/"
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
            assert path.read_bytes() == render_asset(base, behavior, values, manifest["label"]), f"Non-reproducible asset: {path}"
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
                "path": "./rules/v0.1.3/" + path.name,
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
