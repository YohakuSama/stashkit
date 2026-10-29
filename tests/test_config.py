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
        pin = "d63fa06b915d403e2cebc782a8f1551d32b6c927"
        for name, provider in self.profile["rule-providers"].items():
            with self.subTest(provider=name):
                self.assertIn("/" + pin + "/rules/", provider["url"])
                self.assertEqual(provider["path"], "./rules/v0.1.3/" + provider["url"].rsplit("/", 1)[1])
        for group in self.profile["proxy-groups"]:
            self.assertIn("icon", group)
            self.assertIn("/icons/", group["icon"])

    def test_default_proxy_chain_is_reject_until_opt_in(self):
        by_name = {group["name"]: group for group in self.profile["proxy-groups"]}
        self.assertEqual(by_name["Proxy"]["proxies"][0], "REJECT")
        self.assertEqual(by_name["Final"]["proxies"][0], "Proxy")
        self.assertEqual(by_name["ChatGPT"]["proxies"][0], "Proxy")
        self.assertEqual(by_name["AI"]["proxies"][0], "Proxy")
        self.assertEqual(by_name["AdBlock"]["proxies"][0], "REJECT")
        # Even with no node providers and Stash's empty-provider DIRECT
        # substitution, default global/service proxy selection is REJECT.
        self.assertEqual(len(self.profile.get("proxy-providers", {})), 0)

    def test_self_hosted_original_icons_are_pinned(self):
        import hashlib
        import json
        lock = json.loads((ROOT / "build/icon-lock.json").read_text())
        self.assertEqual(len(lock["group_icons"]), 40)
        self.assertEqual(len(lock["asset_git_blob_shas"]), 39)
        self.assertEqual(lock["group_icons"]["ALL"], "Proxy.png")
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


if __name__ == "__main__":
    unittest.main()
