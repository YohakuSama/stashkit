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

    def test_all_40_groups_have_local_node_without_helpers(self):
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
                self.assertNotIn("include-all", group)
                name = group["name"]
                if name in {"Final", "AdBlock"}:
                    self.assertEqual(group, original)
                elif name in {"Auto", "Fallback"}:
                    self.assertEqual(group["proxies"], ["SelfHosted"])
                elif name == "Proxy":
                    self.assertEqual(
                        group["proxies"], ["Auto", "Fallback", "SelfHosted", "REJECT"]
                    )
                elif name == "Steam":
                    self.assertEqual(
                        group["proxies"], ["Proxy", "Auto", "Fallback", "SelfHosted", "DIRECT"]
                    )
                else:
                    self.assertEqual(
                        group["proxies"], original["proxies"] + ["SelfHosted"]
                    )

    def test_dns_and_rules_remain_identical(self):
        for key in ("mode", "log-level", "dns", "rule-providers", "rules"):
            self.assertEqual(self.self_hosted[key], self.canonical[key])
        self.assertEqual(
            sum(rule.startswith("DOMAIN-SUFFIX,") and rule.endswith(",Crypto")
                for rule in self.self_hosted["rules"]),
            29,
        )

    def test_unbound_or_modified_subscription_fails(self):
        with self.assertRaises(ValueError):
            self_hosted_profile(self.source.replace("      - Airport\n", "", 1))
        with self.assertRaises(ValueError):
            self_hosted_profile(self.source.replace(
                "https://example.invalid/REPLACE-WITH-YOUR-CLASH-SUBSCRIPTION",
                "https://example.invalid/different",
            ))


if __name__ == "__main__":
    unittest.main()
