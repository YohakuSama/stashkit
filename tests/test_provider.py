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
        # LoonKit node filters include dynamic nodes in all applicable groups.
        for group in profile["proxy-groups"]:
            if group["name"] in {"AdBlock", "Final"}:
                self.assertNotIn("include-all", group)
            else:
                self.assertIs(group["include-all"], True)
                self.assertEqual(group["filter"], ".*")


if __name__ == "__main__":
    unittest.main()
