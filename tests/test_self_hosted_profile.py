"""Verify the one-file self-hosted profile replaces only the node source."""
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_profiles import self_hosted_profile
from validate_config import validate_profile


class SelfHostedProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "StashKit.yaml").read_text(encoding="utf-8")
        cls.generated = self_hosted_profile(cls.source)
        cls.canonical = yaml.safe_load(cls.source)
        cls.self_hosted = yaml.safe_load(cls.generated)

    def test_output_is_deterministic_and_valid(self):
        self.assertEqual(
            self.generated.encode("utf-8"),
            (ROOT / "StashKit-SelfHosted.yaml").read_bytes(),
        )
        validate_profile(self.self_hosted)
        self.assertNotIn("proxy-providers", self.self_hosted)
        self.assertEqual(self.self_hosted["proxies"], [{
            "name": "SelfHosted",
            "type": "ss",
            "server": "replace-me.invalid",
            "port": 443,
            "cipher": "aes-128-gcm",
            "password": "REPLACE-WITH-YOUR-PASSWORD",
        }])

    def test_all_40_groups_include_any_local_nodes_without_helpers(self):
        expected = self.canonical["proxy-groups"]
        actual = self.self_hosted["proxy-groups"]
        self.assertEqual([group["name"] for group in actual],
                         [group["name"] for group in expected])
        self.assertEqual(len(actual), 40)
        for original, group in zip(expected, actual):
            with self.subTest(group=group["name"]):
                self.assertEqual(group["type"], original["type"])
                self.assertEqual(group.get("icon"), original.get("icon"))
                self.assertNotIn("use", group)
                self.assertEqual(group["proxies"], original["proxies"])
                if group["name"] in {"Final", "AdBlock"}:
                    self.assertEqual(group, original)
                    self.assertNotIn("include-all", group)
                else:
                    self.assertTrue(group["include-all"])

    def test_three_distinct_local_node_names_are_accepted(self):
        from copy import deepcopy
        profile = deepcopy(self.self_hosted)
        profile["proxies"] = [
            {**profile["proxies"][0], "name": name}
            for name in ("HK", "JP", "US")
        ]
        validate_profile(profile)
        self.assertEqual(len(profile["proxies"]), 3)
        for group in profile["proxy-groups"]:
            if group["name"] not in {"Final", "AdBlock"}:
                self.assertTrue(group["include-all"])
                self.assertNotIn("SelfHosted", group.get("proxies", []))

    def test_duplicate_local_node_names_are_rejected(self):
        from copy import deepcopy
        profile = deepcopy(self.self_hosted)
        profile["proxies"] = [dict(profile["proxies"][0])] * 3
        with self.assertRaises(ValueError):
            validate_profile(profile)

    def test_dns_and_rules_remain_identical(self):
        for key in ("mode", "log-level", "dns", "rule-providers", "rules"):
            self.assertEqual(self.self_hosted[key], self.canonical[key])
        self.assertEqual(
            [rule for rule in self.self_hosted["rules"] if rule.endswith(",Crypto")],
            ["DOMAIN,coincheck.com,Crypto", "RULE-SET,Crypto-domain,Crypto"],
        )

    def test_unbound_or_modified_subscription_fails(self):
        with self.assertRaises(ValueError):
            self_hosted_profile(self.source.replace("    use:\n      - Airport\n", "", 1))
        with self.assertRaises(ValueError):
            self_hosted_profile(self.source.replace(
                "https://example.invalid/REPLACE-WITH-YOUR-CLASH-SUBSCRIPTION",
                "https://example.invalid/different",
            ))


if __name__ == "__main__":
    unittest.main()
