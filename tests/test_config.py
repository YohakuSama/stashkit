"""Mutations that the old source-parity validator incorrectly accepted."""
import copy
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify import UniqueKeysLoader
from validate_config import validate_profile, validate_override
from release_meta import RULES_REF, RULES_PATH_PREFIX


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.profile = yaml.load((ROOT / "StashKit.yaml").read_text(), Loader=UniqueKeysLoader)

    def test_shipped_profile_and_provider_override(self):
        validate_profile(self.profile)
        example = yaml.load((ROOT / "overrides/provider.stoverride.example").read_text(), Loader=UniqueKeysLoader)
        validate_override(example)
        merged = copy.deepcopy(self.profile)
        merged["proxy-providers"] = example["proxy-providers"]
        validate_profile(merged)

    def test_all_rules_use_immutable_refs_and_explicit_cache_paths(self):
        pin = RULES_REF
        for name, provider in self.profile["rule-providers"].items():
            with self.subTest(provider=name):
                if provider.get("type") == "inline":
                    self.assertEqual(name, "Private-local")
                    continue
                self.assertIn("/" + pin + "/rules/", provider["url"])
                self.assertEqual(provider["path"], RULES_PATH_PREFIX + provider["url"].rsplit("/", 1)[1])
        for group in self.profile["proxy-groups"]:
            self.assertIn("icon", group)
            self.assertIn("/icons/", group["icon"])

    def test_proxy_uses_flat_native_provider_nodes(self):
        by_name = {group["name"]: group for group in self.profile["proxy-groups"]}
        self.assertEqual(by_name["Proxy"]["proxies"], ["Auto", "Fallback", "REJECT"])
        self.assertEqual(by_name["Proxy"]["use"], ["personal"])
        self.assertNotIn("include-all", by_name["Proxy"])
        self.assertNotIn("filter", by_name["Proxy"])
        self.assertEqual(by_name["ChatGPT"]["proxies"], ["Proxy", "Auto", "Fallback"])
        self.assertEqual(by_name["ChatGPT"]["use"], ["personal"])
        self.assertNotIn("include-all", by_name["ChatGPT"])
        self.assertNotIn("filter", by_name["ChatGPT"])
        self.assertNotIn("ALL", by_name)
        self.assertEqual(len(by_name), 39)
        self.assertEqual(by_name["Final"]["proxies"][0], "Proxy")
        self.assertEqual(by_name["ChatGPT"]["proxies"][0], "Proxy")
        self.assertEqual(by_name["AI"]["proxies"][0], "Proxy")
        self.assertEqual(by_name["AdBlock"]["proxies"][0], "REJECT")
        # Without nodes, Auto and Fallback retain a REJECT fallback.
        # Empty pool behavior must still be checked on Stash iOS.
        self.assertEqual(self.profile["proxy-providers"],
                         {"personal": {"path": "./providers/personal.yaml"}})

    def test_self_hosted_original_icons_are_pinned(self):
        import hashlib
        import json
        lock = json.loads((ROOT / "build/icon-lock.json").read_text())
        self.assertEqual(len(lock["group_icons"]), 39)
        self.assertNotIn("Manual", lock["group_icons"])
        self.assertEqual(len(lock["asset_git_blob_shas"]), 39)
        self.assertNotIn("ALL", lock["group_icons"])
        for name, filename in lock["group_icons"].items():
            group = next(g for g in self.profile["proxy-groups"] if g["name"] == name)
            self.assertEqual(group["icon"], (
                f"https://raw.githubusercontent.com/YohakuSama/stashkit/{lock['icons_commit']}/icons/{filename}"))
            self.assertNotIn("/loonkit/", group["icon"])
        for filename, sha in lock["asset_git_blob_shas"].items():
            with self.subTest(filename=filename):
                raw = (ROOT / "icons" / filename).read_bytes()
                self.assertTrue(raw.startswith(bytes.fromhex("89504e470d0a1a0a")))
                self.assertEqual(hashlib.sha1(
                    b"blob " + str(len(raw)).encode("ascii") + bytes([0]) + raw).hexdigest(), sha)

    def test_self_reference_rejected(self):
        self.profile["proxy-groups"][0]["proxies"] = ["Proxy"]
        with self.assertRaisesRegex(ValueError, "cyclic"):
            validate_profile(self.profile)

    def test_indirect_cycle_rejected(self):
        next(g for g in self.profile["proxy-groups"] if g["name"] == "AI")["proxies"] = ["ChatGPT"]
        next(g for g in self.profile["proxy-groups"] if g["name"] == "ChatGPT")["proxies"] = ["AI"]
        with self.assertRaisesRegex(ValueError, "cyclic"):
            validate_profile(self.profile)

    def test_misspelled_group_type_rejected(self):
        self.profile["proxy-groups"][6]["type"] = "seelct"
        with self.assertRaisesRegex(ValueError, "group type"):
            validate_profile(self.profile)

    def test_unsupported_nested_dns_key_rejected(self):
        self.profile["dns"]["hijack-dns"] = "*:53"
        with self.assertRaisesRegex(ValueError, "unknown StashKit keys"):
            validate_profile(self.profile)

    def test_group_url_rejected(self):
        self.profile["proxy-groups"][1]["url"] = "http://www.bing.com"
        with self.assertRaisesRegex(ValueError, "unknown StashKit keys"):
            validate_profile(self.profile)

    def test_string_boolean_rejected(self):
        self.profile["dns"]["follow-rule"] = "false"
        with self.assertRaisesRegex(ValueError, "boolean"):
            validate_profile(self.profile)

    def test_unknown_policy_and_provider_rejected(self):
        for rule in ("DOMAIN,example.com,Missing", "RULE-SET,missing,Proxy"):
            with self.subTest(rule=rule):
                profile = copy.deepcopy(self.profile)
                profile["rules"].insert(0, rule)
                with self.assertRaisesRegex(ValueError, "Unknown rule"):
                    validate_profile(profile)

    def test_duplicate_yaml_keys_rejected(self):
        with self.assertRaisesRegex(AssertionError, "Duplicate YAML key"):
            yaml.load("dns: {}\ndns: {}\n", Loader=UniqueKeysLoader)

    def test_malformed_rule_values_rejected(self):
        for row in ("DOMAIN,bad domain,Proxy", "DOMAIN-SUFFIX,https://example.com,Proxy",
                    "DOMAIN,a..example.com,Proxy", "GEOIP,NOT-A-COUNTRY,DIRECT",
                    "IP-ASN,4294967296,Proxy", "IP-ASN,0,Proxy", "DOMAIN-REGEX,[,Proxy"):
            with self.subTest(row=row):
                profile = copy.deepcopy(self.profile)
                profile["rules"].insert(-1, row)
                with self.assertRaises(ValueError):
                    validate_profile(profile)

    def test_match_cannot_hide_later_rules(self):
        self.profile["rules"].insert(0, "MATCH,Proxy")
        with self.assertRaisesRegex(ValueError, "MATCH"):
            validate_profile(self.profile)

    def test_dns_collections_must_exist_and_match_domains(self):
        for name in ("missing", "YouTube-ipcidr"):
            with self.subTest(name=name):
                profile = copy.deepcopy(self.profile)
                profile["dns"]["fake-ip-filter"].append("rule-set:" + name)
                with self.assertRaises(ValueError):
                    validate_profile(profile)

    def test_malformed_inline_provider_is_rejected(self):
        for key, value in (("payload", ["DOMAIN,bad domain"]), ("url", "https://example.com"),
                           ("payload", ["DOMAIN-REGEX,["])):
            with self.subTest(key=key, value=value):
                profile = copy.deepcopy(self.profile)
                profile["rule-providers"]["Private-local"][key] = value
                with self.assertRaises(ValueError):
                    validate_profile(profile)


if __name__ == "__main__":
    unittest.main()
