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
        results.append((name.strip(), parts[0], choices, has_nodes))
    return results


class PolicyGroupParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expected = expected_groups()
        assert len(cls.expected) == 39

    def test_all_profiles_match_upstream_policy_choices(self):
        for filename in ("StashKit.yaml", "StashKit-Privacy.yaml", "StashKit-Local.yaml"):
            with self.subTest(profile=filename):
                profile = yaml.safe_load((ROOT / filename).read_text(encoding="utf-8"))
                validate_profile(profile)
                groups = profile["proxy-groups"]
                self.assertEqual(len(groups), 39)
                self.assertEqual([g["name"] for g in groups],
                                 [row[0] for row in self.expected])
                self.assertFalse({"ALL", "Manual"} & {g["name"] for g in groups})
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
            "Microsoft": ["DIRECT", "Proxy", "Auto", "Fallback"],
            "Apple": ["DIRECT", "Proxy", "Auto", "Fallback"],
            "Speedtest": ["DIRECT", "Proxy", "Auto", "Fallback"],
            "Bilibili": ["DIRECT", "Proxy", "Auto", "Fallback"],
            "Line": ["DIRECT", "Proxy", "Auto", "Fallback"],
            "Steam": ["Proxy", "Auto", "Fallback", "DIRECT"],
        }
        for filename in ("StashKit.yaml", "StashKit-Privacy.yaml", "StashKit-Local.yaml"):
            profile = yaml.safe_load((ROOT / filename).read_text(encoding="utf-8"))
            groups = {g["name"]: g for g in profile["proxy-groups"]}
            for name, choices in expected.items():
                with self.subTest(profile=filename, group=name):
                    self.assertEqual(groups[name]["proxies"], choices)
                    self.assertTrue(groups[name]["include-all"])
                    self.assertEqual(groups[name]["filter"], ".*")
            self.assertNotIn("DIRECT", groups["Proxy"]["proxies"])
            for name in ("AI", "ChatGPT", "Gemini", "Claude"):
                self.assertNotIn("DIRECT", groups[name]["proxies"])
            self.assertEqual(groups["AdBlock"]["proxies"][0], "REJECT")
            self.assertEqual(groups["Final"]["proxies"][0], "Proxy")

    def test_proxy_and_services_mix_named_policies_with_dynamic_nodes(self):
        profile = yaml.safe_load((ROOT / "StashKit.yaml").read_text(encoding="utf-8"))
        groups = {g["name"]: g for g in profile["proxy-groups"]}
        self.assertEqual(groups["Proxy"]["proxies"], ["Auto", "Fallback"])
        self.assertTrue(groups["Proxy"]["include-all"])
        self.assertEqual(groups["Proxy"]["filter"], ".*")
        for name in ("AI", "ChatGPT", "Gemini", "GitHub", "YouTube", "Netflix", "Steam"):
            with self.subTest(group=name):
                group = groups[name]
                self.assertEqual(group["filter"], ".*")
                self.assertTrue(group["include-all"])
                self.assertTrue({"Proxy", "Auto", "Fallback"} <= set(group["proxies"]))
        self.assertEqual(groups["ChatGPT"]["proxies"], ["Proxy", "Auto", "Fallback"])
        for name in ("AdBlock", "Final"):
            self.assertNotIn("include-all", groups[name])


if __name__ == "__main__":
    unittest.main()
