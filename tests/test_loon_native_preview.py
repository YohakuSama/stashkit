"""Experimental Stash iOS selector preview: structural parity is not runtime UI parity."""
import copy
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_config import validate_profile


class LoonNativePreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.production = yaml.safe_load((ROOT / "StashKit.yaml").read_text(encoding="utf-8"))
        cls.preview = yaml.safe_load((ROOT / "StashKit-Loon-Native-Preview.yaml").read_text(
            encoding="utf-8"))
        upstream = (ROOT / "upstream/loonkit/LoonKit.lcf").read_text(encoding="utf-8")
        groups = upstream.split("[Proxy Group]", 1)[1].split("[Remote Rule]", 1)[0]
        cls.upstream_rows = [line for line in groups.splitlines() if " = " in line]

    def test_standalone_preview_validates_and_preserves_every_other_section(self):
        validate_profile(self.preview)
        base = copy.deepcopy(self.production)
        candidate = copy.deepcopy(self.preview)
        base.pop("proxy-groups")
        candidate.pop("proxy-groups")
        self.assertEqual(candidate, base)

    def test_39_exact_upstream_groups_no_all_or_manual(self):
        actual = self.preview["proxy-groups"]
        self.assertEqual(len(actual), 39)
        self.assertEqual([row["name"] for row in actual],
                         [row.split(" = ", 1)[0] for row in self.upstream_rows])
        self.assertNotIn("Manual", {row["name"] for row in actual})
        self.assertNotIn("ALL", {row["name"] for row in actual})
        self.assertFalse(self.preview.get("proxy-providers"))
        self.assertFalse(self.preview.get("proxies"))

    def test_proxy_explicitly_selects_auto_and_fallback_and_dynamic_nodes(self):
        groups = {group["name"]: group for group in self.preview["proxy-groups"]}
        self.assertEqual(groups["Proxy"]["type"], "select")
        self.assertEqual(groups["Proxy"]["proxies"], ["Auto", "Fallback"])
        self.assertIs(groups["Proxy"]["include-all"], True)
        self.assertEqual(groups["Proxy"]["filter"], ".*")
        for name, kind in (("Auto", "url-test"), ("Fallback", "fallback")):
            self.assertEqual(groups[name]["type"], kind)
            self.assertTrue(groups[name]["include-all"])
            self.assertEqual(groups[name]["proxies"], ["REJECT"])

    def test_each_service_keeps_its_loon_named_strategies_and_dynamic_nodes(self):
        groups = {group["name"]: group for group in self.preview["proxy-groups"]}
        service_names = set(groups) - {"Proxy", "Auto", "Fallback", "AdBlock", "Final"}
        self.assertEqual(len(service_names), 34)
        for name in service_names:
            with self.subTest(group=name):
                actual = groups[name]
                self.assertTrue(actual["include-all"])
                self.assertEqual(actual["filter"], ".*")
                source = next(row for row in self.upstream_rows if row.startswith(name + " = "))
                policy_options = source.split(" = ", 1)[1].split(",img-url", 1)[0].split(",")[1:]
                expected = [x.strip() for x in policy_options if x.strip() != "ALL_Filter"]
                self.assertEqual(actual["proxies"], expected)
                self.assertIn("Proxy", actual["proxies"])
                self.assertIn("Auto", actual["proxies"])
                self.assertIn("Fallback", actual["proxies"])
        for name in ("AdBlock", "Final"):
            self.assertNotIn("include-all", groups[name])

    def test_only_dynamic_member_collection_differs_from_production(self):
        prior = {x["name"]: x for x in self.production["proxy-groups"]}
        for group in self.preview["proxy-groups"]:
            name = group["name"]
            if name in {"Proxy", "Auto", "Fallback"}:
                continue
            original = copy.deepcopy(prior[name])
            if name not in {"AdBlock", "Final"}:
                group = copy.deepcopy(group)
                group.pop("include-all")
                group.pop("filter")
            self.assertEqual(group, original)


if __name__ == "__main__":
    unittest.main()
