"""Ensure the public self-hosted profile cannot lose manual choices on node refresh."""
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_profiles import self_hosted_profile
from build_loon_selection import build_loon_selection
from validate_config import validate_profile


def fixture_node(name):
    return {
        "name": name, "type": "ss", "server": "192.0.2.10",
        "port": 443, "cipher": "aes-128-gcm", "password": "TEST-ONLY",
    }


class SelfHostedProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "StashKit.yaml").read_text(encoding="utf-8")
        cls.generated = self_hosted_profile(cls.source)
        cls.canonical = yaml.safe_load(cls.source)
        cls.self_hosted = yaml.safe_load(cls.generated)

    def test_one_placeholder_node_is_explicit_and_no_dynamic_discovery(self):
        self.assertEqual(self.generated.encode("utf-8"),
                         (ROOT / "StashKit-SelfHosted.yaml").read_bytes())
        validate_profile(self.self_hosted)
        self.assertNotIn("proxy-providers", self.self_hosted)
        self.assertEqual(self.self_hosted["proxies"], [{
            "name": "SelfHosted", "type": "ss", "server": "replace-me.invalid",
            "port": 443, "cipher": "aes-128-gcm",
            "password": "REPLACE-WITH-YOUR-PASSWORD",
        }])
        self.assertEqual(len(self.self_hosted["proxy-groups"]), 40)
        expected = {g["name"]: g for g in self.canonical["proxy-groups"]}
        for group in self.self_hosted["proxy-groups"]:
            name = group["name"]
            with self.subTest(name=name):
                self.assertEqual(group["type"], expected[name]["type"])
                self.assertEqual(group["icon"], expected[name]["icon"])
                self.assertFalse({"use", "use-url", "include-all", "filter"} & set(group))
                suffix = [] if name in {"AdBlock", "Final"} else ["SelfHosted"]
                self.assertEqual(group["proxies"], expected[name]["proxies"] + suffix)
        groups = {group["name"]: group for group in self.self_hosted["proxy-groups"]}
        self.assertEqual(groups["Proxy"]["proxies"],
                         ["Auto", "Fallback", "REJECT", "SelfHosted"])
        self.assertEqual(groups["Auto"]["proxies"], ["SelfHosted"])
        self.assertEqual(groups["Fallback"]["proxies"], ["SelfHosted"])

    def test_generator_expands_arbitrary_user_nodes_without_hardcoding(self):
        for names in (["Home"], ["JP", "US", "HK"], ["Any other node", "Another"]):
            with self.subTest(names=names):
                nodes = [fixture_node(name) for name in names]
                profile = build_loon_selection(self.canonical, nodes=nodes, layout="native")
                validate_profile(profile)
                self.assertEqual(profile["proxies"], nodes)
                self.assertNotIn("proxy-providers", profile)
                self.assertEqual(len(profile["proxy-groups"]), 40)
                self.assertEqual(profile["rule-providers"], self.canonical["rule-providers"])
                self.assertEqual(profile["rules"], self.canonical["rules"])
                groups = {g["name"]: g for g in profile["proxy-groups"]}
                self.assertEqual(groups["Proxy"]["proxies"],
                                 ["Auto", "Fallback", "REJECT"] + names)
                self.assertEqual(groups["Auto"]["proxies"], names)
                self.assertEqual(groups["Fallback"]["proxies"], names)
                for g in groups.values():
                    self.assertFalse({"use", "use-url", "include-all"} & set(g))
                    if g["name"] not in {"AdBlock", "Final", "Proxy", "Auto", "Fallback"}:
                        self.assertEqual(g["proxies"][-len(names):], names)

    def test_duplicate_private_node_names_are_rejected(self):
        with self.assertRaises(ValueError):
            build_loon_selection(self.canonical, nodes=[fixture_node("HK")] * 2,
                                 layout="native")

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
