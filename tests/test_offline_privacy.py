"""Verify offline package and opt-in privacy mode against Stash documented semantics."""
import sys
import unittest
import zipfile
import io
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_offline_bundle import make_zip, local_profile
from validate_config import validate_profile


class OfflineAndPrivacyTests(unittest.TestCase):
    def test_bundle_contains_every_rule_and_matches_committed_profile(self):
        binary = make_zip()
        with zipfile.ZipFile(io.BytesIO(binary)) as archive:
            names = archive.namelist()
            self.assertEqual(len([n for n in names if n.startswith("rules/")]), 54)
            self.assertEqual(len(names), 57)
            self.assertEqual(archive.read("StashKit-Local.yaml"),
                             (ROOT / "StashKit-Local.yaml").read_bytes())
            profile = yaml.safe_load(archive.read("StashKit-Local.yaml"))
            self.assertEqual(len(profile["rule-providers"]), 54)
            for provider in profile["rule-providers"].values():
                self.assertNotIn("url", provider)
                self.assertNotIn("interval", provider)
                self.assertTrue(provider["path"].startswith("./rules/"))
            validate_profile(profile)

    def test_bundle_is_byte_reproducible(self):
        self.assertEqual(make_zip(), make_zip())

    def test_privacy_dns_override_prefix_and_bootstrap(self):
        profile = yaml.safe_load((ROOT / "StashKit.yaml").read_text())
        override = yaml.safe_load((ROOT / "overrides/dns-privacy.stoverride.example").read_text())
        self.assertEqual(override["dns"], {"follow-rule": True})
        self.assertEqual(override["rules"], ["DOMAIN,dns.alidns.com,Proxy"])
        profile["dns"].update(override["dns"])
        profile["rules"] = override["rules"] + profile["rules"]
        validate_profile(profile)
        self.assertEqual(profile["rules"][0], "DOMAIN,dns.alidns.com,Proxy")
        self.assertEqual(profile["dns"]["proxy-server-nameserver"],
                         ["https://223.5.5.5/dns-query"])
        self.assertEqual(profile["dns"]["nameserver-policy"]["geosite:private"], "system")


if __name__ == "__main__":
    unittest.main()
