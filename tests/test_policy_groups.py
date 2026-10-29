"""Validate policy choices against the Stash UI and the pinned LoonKit group list."""
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream/loonkit/LoonKit.lcf"
sys.path.insert(0, str(ROOT / "scripts"))
from validate_config import validate_profile


def expected_groups():
    profile = UPSTREAM.read_text(encoding="utf-8")
    source = profile.split("[Proxy Group]", 1)[1].split("[Remote Rule]", 1)[0]
    groups = []
    for line in source.splitlines():
        if " = " not in line:
            continue
        name, body = line.split("=", 1)
        items = [item.strip() for item in body.split(",img-url", 1)[0].split(",")]
        kind = items[0]
        filters = {"ALL_Filter", "Auto_Filter", "Fallback_Filter"}
        children = [item for item in items[1:]
                    if item not in filters and "=" not in item]
        uses_node_pool = name.strip() in {"Proxy", "Auto", "Fallback"}
        if uses_node_pool:
            children = ["REJECT"]
        groups.append((name.strip(), kind, children, uses_node_pool))
    return groups


class PolicyGroupParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expected = expected_groups()
        assert len(cls.expected) == 39

    def test_all_profiles_match_upstream_group_semantics(self):
        for filename in ("StashKit.yaml", "StashKit-Privacy.yaml", "StashKit-Local.yaml"):
            with self.subTest(profile=filename):
                profile = yaml.safe_load((ROOT / filename).read_text(encoding="utf-8"))
                validate_profile(profile)
                groups = profile["proxy-groups"]
                self.assertEqual([group["name"] for group in groups],
                                 [row[0] for row in self.expected])
                self.assertNotIn("ALL", {group["name"] for group in groups})
                for group, (name, kind, children, include_all) in zip(groups, self.expected):
                    with self.subTest(profile=filename, group=name):
                        self.assertEqual(group["type"], kind)
                        self.assertEqual(group["proxies"], children)
                        self.assertEqual(group.get("include-all", False), include_all)

    def test_service_groups_expose_named_strategies_without_node_only_mode(self):
        profile = yaml.safe_load((ROOT / "StashKit.yaml").read_text(encoding="utf-8"))
        by_name = {group["name"]: group for group in profile["proxy-groups"]}
        self.assertEqual(by_name["Proxy"]["proxies"], ["REJECT"])
        self.assertTrue(by_name["Proxy"]["include-all"])
        for name in ("AI", "ChatGPT", "Gemini", "GitHub", "YouTube", "Netflix", "Steam"):
            with self.subTest(group=name):
                group = by_name[name]
                self.assertNotIn("include-all", group)
                self.assertEqual(group["proxies"][:3], ["Proxy", "Auto", "Fallback"])
                self.assertNotIn("ALL", group["proxies"])
        for name in ("AdBlock", "Final"):
            self.assertNotIn("include-all", by_name[name])


    def test_every_profile_can_show_auto_and_fallback_for_services(self):
        for filename in ("StashKit.yaml", "StashKit-Privacy.yaml", "StashKit-Local.yaml"):
            with self.subTest(profile=filename):
                profile = yaml.safe_load((ROOT / filename).read_text(encoding="utf-8"))
                groups = {group["name"]: group for group in profile["proxy-groups"]}
                for name, group in groups.items():
                    if name in {"Proxy", "Auto", "Fallback"}:
                        self.assertTrue(group.get("include-all"))
                        self.assertFalse(set(group["proxies"]) & set(groups))
                    else:
                        self.assertNotIn("include-all", group)
                        if name not in {"AdBlock", "Final"}:
                            self.assertIn("Auto", group["proxies"])
                            self.assertIn("Fallback", group["proxies"])
                            self.assertIn("Proxy", group["proxies"])
                self.assertEqual(groups["ChatGPT"]["proxies"],
                                 ["Proxy", "Auto", "Fallback"])


if __name__ == "__main__":
    unittest.main()
