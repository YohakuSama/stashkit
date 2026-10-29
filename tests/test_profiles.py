"""Check deterministic profile variants and reject undocumented configuration drift."""
import copy
import re
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_profiles import local_profile, privacy_profile
from validate_config import validate_profile


class ProfileVariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "StashKit.yaml").read_text(encoding="utf-8")

    def test_generated_variants_match_committed_files(self):
        for name, render in (("StashKit-Privacy.yaml", privacy_profile),
                             ("StashKit-Local.yaml", local_profile)):
            with self.subTest(profile=name):
                result = render(self.source)
                self.assertEqual(result.encode("utf-8"), (ROOT / name).read_bytes())
                validate_profile(yaml.safe_load(result))

    def test_privacy_variant_changes_only_documented_dns_and_route(self):
        original = yaml.safe_load(self.source)
        private = yaml.safe_load(privacy_profile(self.source))
        self.assertFalse(original["dns"]["follow-rule"])
        self.assertTrue(private["dns"]["follow-rule"])
        private["dns"]["follow-rule"] = False
        self.assertEqual(private["rules"].pop(0), "DOMAIN,dns.alidns.com,Proxy")
        self.assertEqual(private, original)

    def test_local_variant_only_removes_remote_provider_fetches(self):
        original = yaml.safe_load(self.source)
        local = yaml.safe_load(local_profile(self.source))
        for provider in original["rule-providers"].values():
            provider.pop("url", None)
            provider.pop("interval", None)
        self.assertEqual(local, original)

    def test_missing_source_sections_fail_closed(self):
        for bad, render in (
            (self.source.replace("  follow-rule: false\n", ""), privacy_profile),
            (self.source.replace("rules:\n", "routes:\n"), privacy_profile),
            (self.source.replace("rule-providers:\n", "providers:\n"), local_profile),
            (self.source.replace("    interval: 86400\n", "", 1), local_profile),
        ):
            with self.subTest(render=render.__name__):
                with self.assertRaises(ValueError):
                    render(bad)

    def test_yaml_comments_are_concise_and_english(self):
        for name in ("StashKit.yaml", "StashKit-Privacy.yaml", "StashKit-Local.yaml"):
            comments = [line.strip() for line in (ROOT / name).read_text().splitlines()
                        if line.lstrip().startswith("#")]
            with self.subTest(profile=name):
                self.assertLessEqual(len(comments), 8)
                self.assertFalse(any(re.search(r"[\u4e00-\u9fff]", line) for line in comments))
                self.assertTrue(all(len(line) <= 100 for line in comments))


if __name__ == "__main__":
    unittest.main()
