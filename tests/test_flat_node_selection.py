"""Regression tests for private static node expansion without a published template."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_loon_selection import build_loon_selection
from validate_config import validate_profile


def fixture_node(name):
    return {"name": name, "type": "ss", "server": "192.0.2.10", "port": 443,
            "cipher": "aes-128-gcm", "password": "TEST-ONLY"}


class FlatNodesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = yaml.safe_load((ROOT / "StashKit.yaml").read_text())

    def test_explicit_members_for_arbitrary_names(self):
        for names in (["Home"], ["JP", "US", "HK"], ["Any other node", "Another"]):
            with self.subTest(names=names):
                nodes = [fixture_node(name) for name in names]
                profile = build_loon_selection(self.template, nodes=nodes, layout="native")
                validate_profile(profile)
                self.assertEqual(profile["proxies"], nodes)
                self.assertNotIn("proxy-providers", profile)
                self.assertEqual(len(profile["proxy-groups"]), 40)
                self.assertEqual(profile["rule-providers"], self.template["rule-providers"])
                self.assertEqual(profile["rules"], self.template["rules"])
                groups = {g["name"]: g for g in profile["proxy-groups"]}
                self.assertEqual(groups["Proxy"]["proxies"], ["Auto", "Fallback", "REJECT"] + names)
                self.assertEqual(groups["Auto"]["proxies"], names)
                self.assertEqual(groups["Fallback"]["proxies"], names)
                for group in groups.values():
                    self.assertFalse({"use", "use-url", "include-all"} & set(group))
                    if group["name"] not in {"AdBlock", "Final", "Proxy", "Auto", "Fallback"}:
                        self.assertEqual(group["proxies"][-len(names):], names)

    def test_cli_accepts_complete_private_node_sources(self):
        with tempfile.TemporaryDirectory(dir=ROOT.parent) as temp:
            folder = Path(temp)
            source, target = folder / "nodes-source.yaml", folder / "StashKit-Personal.yaml"
            names = ["test-vless-node", "test-hy2-node", "test-mieru-node"]
            source.write_text(yaml.safe_dump({"proxies": [fixture_node(n) for n in names]}))
            result = subprocess.run([
                sys.executable, str(ROOT / "scripts/build_loon_selection.py"),
                "--layout", "flat", "--nodes-from", str(source), "--output", str(target)
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            profile = yaml.safe_load(target.read_text())
            validate_profile(profile)
            groups = {g["name"]: g for g in profile["proxy-groups"]}
            self.assertEqual(groups["Proxy"]["proxies"], ["Auto", "Fallback", "REJECT"] + names)
            self.assertEqual(groups["Auto"]["proxies"], names)
            self.assertEqual(groups["Fallback"]["proxies"], names)

    def test_duplicate_private_names_are_rejected(self):
        with self.assertRaises(ValueError):
            build_loon_selection(self.template, nodes=[fixture_node("HK")] * 2, layout="native")


if __name__ == "__main__":
    unittest.main()
