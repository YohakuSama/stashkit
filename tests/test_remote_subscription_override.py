"""Remote StashKit overlay keeps the user's subscribed nodes and matches Loon policy choices."""
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_profiles import remote_subscription_override
from validate_config import validate_profile


class RemoteSubscriptionOverrideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "StashKit.yaml").read_text(encoding="utf-8")
        cls.original = yaml.safe_load(cls.source)

    def test_deterministic_remote_file_and_replacement_markers(self):
        content = remote_subscription_override(self.source)
        self.assertEqual(content.encode("utf-8"), (ROOT / "StashKit.stoverride").read_bytes())
        for key in ("dns", "proxy-groups", "rule-providers", "rules"):
            self.assertEqual(content.count(f"\n{key}: #!replace\n"), 1)
        self.assertEqual(content.count("    include-all: true\n"), 37)
        self.assertNotIn("    use: []\n", content)

    def test_all_loon_node_filters_become_live_all_node_selectors(self):
        override = yaml.safe_load(remote_subscription_override(self.source))
        self.assertNotIn("proxies", override)
        self.assertNotIn("proxy-providers", override)
        override.pop("name")
        override.pop("desc")
        validate_profile(override)
        original_groups = self.original["proxy-groups"]
        derived_groups = override["proxy-groups"]
        self.assertEqual(len(derived_groups), 39)
        self.assertEqual([g["name"] for g in derived_groups],
                         [g["name"] for g in original_groups])
        for before, after in zip(original_groups, derived_groups):
            with self.subTest(group=before["name"]):
                self.assertEqual(before["proxies"], after["proxies"])
                self.assertEqual(before["type"], after["type"])
                self.assertEqual(before.get("icon"), after.get("icon"))
                self.assertNotIn("use", after)
                self.assertEqual(after.get("include-all", False),
                                 before["name"] not in {"AdBlock", "Final"})
        for key in ("rules", "rule-providers", "dns"):
            self.assertEqual(override[key], self.original[key])

    def test_source_drift_fails_instead_of_shipping_empty_selectors(self):
        broken = self.source.replace("    use: []\n", "", 1)
        with self.assertRaises(ValueError):
            remote_subscription_override(broken)


if __name__ == "__main__":
    unittest.main()
