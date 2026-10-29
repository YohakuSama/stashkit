"""Regression tests for provider-aware Stash policy groups matching LoonKit behavior."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_loon_selection import (NODE_POOLS, PROFILE_FILES, build_loon_selection,
                                  read_provider_override)
from validate_config import validate_profile

PROVIDERS = {
    "personal": {
        "url": "https://example.org/node-provider.yaml",
        "interval": 3600,
        "benchmark-url": "http://www.bing.com",
        "benchmark-timeout": 5,
    },
    "backup": {
        "url": "https://example.org/backup-provider.yaml",
        "interval": 3600,
    },
}


class LoonSelectionTests(unittest.TestCase):
    def test_provider_groups_preserve_policies_and_allow_direct_node_selection(self):
        for profile_name in PROFILE_FILES.values():
            with self.subTest(profile=profile_name):
                original = yaml.safe_load((ROOT / profile_name).read_text(encoding="utf-8"))
                snapshot = copy.deepcopy(original)
                generated = build_loon_selection(original, PROVIDERS)
                validate_profile(generated)
                self.assertEqual(original, snapshot)
                for key in ("dns", "rules", "rule-providers", "mode", "log-level"):
                    self.assertEqual(generated[key], original[key])
                self.assertEqual(generated["proxy-providers"], PROVIDERS)
                by_name = {row["name"]: row for row in generated["proxy-groups"]}
                self.assertEqual(len(by_name), 39)
                self.assertNotIn("ALL", by_name)
                self.assertEqual(by_name["Proxy"]["proxies"],
                                 ["REJECT", "Auto", "Fallback"])
                self.assertEqual(by_name["Auto"]["proxies"], ["REJECT"])
                self.assertEqual(by_name["Fallback"]["proxies"], ["REJECT"])
                for name, group in by_name.items():
                    self.assertNotIn("include-all", group)
                    if name in {"AdBlock", "Final"}:
                        self.assertNotIn("use", group)
                    else:
                        self.assertEqual(group["use"], list(PROVIDERS))
                    if name not in NODE_POOLS | {"AdBlock", "Final"}:
                        self.assertTrue({"Proxy", "Auto", "Fallback"} <= set(group["proxies"]))
                self.assertEqual(by_name["ChatGPT"]["proxies"],
                                 ["Proxy", "Auto", "Fallback"])

    def test_missing_and_conflicting_providers_fail(self):
        source = yaml.safe_load((ROOT / "StashKit.yaml").read_text(encoding="utf-8"))
        with self.assertRaisesRegex(ValueError, "Named providers"):
            build_loon_selection(source, {})
        with self.assertRaisesRegex(ValueError, "conflict"):
            build_loon_selection(source, {"Proxy": PROVIDERS["personal"]})
        malformed = copy.deepcopy(source)
        malformed["proxy-groups"] = malformed["proxy-groups"][1:]
        with self.assertRaisesRegex(ValueError, "Unexpected canonical"):
            build_loon_selection(malformed, PROVIDERS)

    def test_provider_override_validates_user_input_and_never_accepts_example(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "providers.stoverride"
            path.write_text(yaml.safe_dump({
                "name": "Personal node providers",
                "proxy-providers": PROVIDERS,
            }), encoding="utf-8")
            self.assertEqual(read_provider_override(path), PROVIDERS)
            path.write_text(yaml.safe_dump({
                "proxy-providers": {"personal": {
                    "url": "https://example.invalid/REPLACE-WITH-YOUR-SUBSCRIPTION",
                }},
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Replace the example"):
                read_provider_override(path)
            path.write_text(yaml.safe_dump({
                "proxy-providers": PROVIDERS,
                "rules": ["MATCH,DIRECT"],
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Expected an override"):
                read_provider_override(path)

    def test_private_output_folder_is_gitignored(self):
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("dist/", ignore)
        self.assertIn("*.stoverride", ignore)


if __name__ == "__main__":
    unittest.main()
