"""The example must use Stash's node/provider latency test parameters."""
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class ProviderTests(unittest.TestCase):
    def test_benchmark_is_on_provider_not_groups(self):
        example = yaml.safe_load((ROOT / "overrides/provider.stoverride.example").read_text())
        provider = example["proxy-providers"]["personal"]
        self.assertEqual(provider["benchmark-url"], "http://www.bing.com")
        self.assertEqual(provider["benchmark-timeout"], 5)
        profile = yaml.safe_load((ROOT / "StashKit.yaml").read_text())
        for group in profile["proxy-groups"]:
            with self.subTest(group=group["name"]):
                self.assertNotIn("url", group)
        # All selectable native groups reference the same local provider.
        self.assertEqual(profile["proxy-providers"]["personal"],
                         {"path": "./providers/personal.yaml"})
        for group in profile["proxy-groups"]:
            self.assertNotIn("include-all", group)
            self.assertNotIn("filter", group)
            if group["name"] not in {"AdBlock", "Final"}:
                self.assertEqual(group["use"], ["personal"])
            else:
                self.assertNotIn("use", group)


if __name__ == "__main__":
    unittest.main()
