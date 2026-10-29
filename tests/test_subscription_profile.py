"""Check the directly editable provider profile retains the canonical 39 policies."""
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_profiles import subscription_profile
from validate_config import validate_profile


class SubscriptionProfileTests(unittest.TestCase):
    def test_single_provider_profile_matches_generator_and_is_valid(self):
        source = (ROOT / "StashKit.yaml").read_text(encoding="utf-8")
        generated = subscription_profile(source)
        self.assertEqual((ROOT / "StashKit-Subscription.yaml").read_bytes(), generated.encode("utf-8"))
        data = yaml.safe_load(generated)
        canonical = yaml.safe_load(source)
        validate_profile(data)
        for key in ("dns", "rules", "rule-providers"):
            self.assertEqual(data[key], canonical[key])
        groups = {item["name"]: item for item in data["proxy-groups"]}
        self.assertEqual(len(groups), 39)
        self.assertEqual(groups["Proxy"]["proxies"], ["Auto", "Fallback", "REJECT"])
        self.assertEqual(groups["Auto"]["proxies"], [])
        self.assertEqual(groups["Fallback"]["proxies"], [])
        self.assertEqual(groups["ChatGPT"]["proxies"], ["Proxy", "Auto", "Fallback"])
        self.assertNotIn("proxies", data)
        self.assertEqual(
            data["proxy-providers"]["Airport"]["url"],
            "https://example.invalid/REPLACE-WITH-YOUR-CLASH-SUBSCRIPTION",
        )
        for name, group in groups.items():
            with self.subTest(name=name):
                self.assertNotIn("include-all", group)
                if name in {"AdBlock", "Final"}:
                    self.assertNotIn("use", group)
                else:
                    self.assertEqual(group["use"], ["Airport"])

    def test_does_not_silently_omit_a_binding(self):
        source = (ROOT / "StashKit.yaml").read_text(encoding="utf-8")
        with self.assertRaises(ValueError):
            subscription_profile(source.replace("    use: []\n", "", 1))


if __name__ == "__main__":
    unittest.main()
