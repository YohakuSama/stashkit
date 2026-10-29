"""Compare published Stash policy groups with the pinned LoonKit selectors."""
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream/loonkit/LoonKit.lcf"
sys.path.insert(0, str(ROOT / "scripts"))
from validate_config import validate_profile


def expected_groups():
    upstream = UPSTREAM.read_text(encoding="utf-8")
    section = upstream.split("[Proxy Group]", 1)[1].split("[Remote Rule]", 1)[0]
    results = []
    for row in section.splitlines():
        if " = " not in row:
            continue
        name, body = row.split("=", 1)
        parts = [x.strip() for x in body.split(",img-url", 1)[0].split(",")]
        node_filters = {"ALL_Filter", "Auto_Filter", "Fallback_Filter"}
        has_nodes = any(x in node_filters for x in parts[1:])
        choices = [x for x in parts[1:] if x not in node_filters and "=" not in x]
        if name.strip() in {"Auto", "Fallback"}:
            choices = ["REJECT"]  # Empty dynamic node pool fallback
        group_name = name.strip()
        if group_name == "Proxy":
            choices.append("ALL")
            has_nodes = False
        elif group_name not in {"Auto", "Fallback", "AdBlock", "Final"}:
            choices.append("ALL")
            has_nodes = False
        results.append((group_name, parts[0], choices, has_nodes))
        if group_name == "Fallback":
            results.append(("ALL", "select", ["REJECT"], True))
    return results


class PolicyGroupParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expected = expected_groups()
        assert len(cls.expected) == 40

    def test_all_profiles_match_upstream_policy_choices(self):
        for filename in ("StashKit.yaml", "StashKit-Privacy.yaml", "StashKit-Local.yaml"):
            with self.subTest(profile=filename):
                profile = yaml.safe_load((ROOT / filename).read_text(encoding="utf-8"))
                validate_profile(profile)
                groups = profile["proxy-groups"]
                self.assertEqual(len(groups), 40)
                self.assertEqual([g["name"] for g in groups],
                                 [row[0] for row in self.expected])
                self.assertIn("ALL", {g["name"] for g in groups})
                self.assertNotIn("Manual", {g["name"] for g in groups})
                for group, (name, kind, choices, has_nodes) in zip(groups, self.expected):
                    with self.subTest(group=name):
                        self.assertEqual(group["type"], kind)
                        self.assertEqual(group["proxies"], choices)
                        self.assertEqual(group.get("include-all", False), has_nodes)
                        if has_nodes:
                            self.assertEqual(group.get("filter"), ".*")
                        else:
                            self.assertNotIn("filter", group)

    def test_direct_capable_service_groups_preserve_loon_choices(self):
        # Exactly the six service selectors that allow manual DIRECT in LoonKit.
        expected = {
            "Microsoft": ["DIRECT", "Proxy", "Auto", "Fallback", "ALL"],
            "Apple": ["DIRECT", "Proxy", "Auto", "Fallback", "ALL"],
            "Speedtest": ["DIRECT", "Proxy", "Auto", "Fallback", "ALL"],
            "Bilibili": ["DIRECT", "Proxy", "Auto", "Fallback", "ALL"],
            "Line": ["DIRECT", "Proxy", "Auto", "Fallback", "ALL"],
            "Steam": ["Proxy", "Auto", "Fallback", "ALL", "DIRECT"],
        }
        for filename in ("StashKit.yaml", "StashKit-Privacy.yaml", "StashKit-Local.yaml"):
            profile = yaml.safe_load((ROOT / filename).read_text(encoding="utf-8"))
            groups = {g["name"]: g for g in profile["proxy-groups"]}
            for name, choices in expected.items():
                with self.subTest(profile=filename, group=name):
                    self.assertEqual(groups[name]["proxies"], choices)
                    self.assertNotIn("include-all", groups[name])
                    self.assertNotIn("filter", groups[name])
            self.assertNotIn("DIRECT", groups["Proxy"]["proxies"])
            for name in ("AI", "ChatGPT", "Gemini", "Claude"):
                self.assertNotIn("DIRECT", groups[name]["proxies"])
            self.assertEqual(groups["AdBlock"]["proxies"][0], "REJECT")
            self.assertEqual(groups["Final"]["proxies"][0], "Proxy")

    def test_proxy_and_services_mix_named_policies_with_dynamic_nodes(self):
        profile = yaml.safe_load((ROOT / "StashKit.yaml").read_text(encoding="utf-8"))
        groups = {g["name"]: g for g in profile["proxy-groups"]}
        self.assertEqual(groups["Proxy"]["proxies"], ["Auto", "Fallback", "ALL"])
        self.assertNotIn("include-all", groups["Proxy"])
        for name in ("AI", "ChatGPT", "Gemini", "GitHub", "YouTube", "Netflix", "Steam"):
            with self.subTest(group=name):
                group = groups[name]
                self.assertNotIn("filter", group)
                self.assertNotIn("include-all", group)
                self.assertTrue({"Proxy", "Auto", "Fallback", "ALL"} <= set(group["proxies"]))
        self.assertEqual(groups["ChatGPT"]["proxies"], ["Proxy", "Auto", "Fallback", "ALL"])
        for name in ("Auto", "Fallback", "ALL"):
            self.assertTrue(groups[name]["include-all"])
            self.assertEqual(groups[name]["filter"], ".*")
        for name in ("AdBlock", "Final"):
            self.assertNotIn("include-all", groups[name])


if __name__ == "__main__":
    unittest.main()
