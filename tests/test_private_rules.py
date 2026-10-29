"""Keep private scope pinned and preserve the original GeoSite matching kinds."""
import re
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from private_rules import private_provider, NAME, SOURCE_SINGLE_LABEL, SINGLE_LABEL


class PrivateRulesTests(unittest.TestCase):
    def test_every_profile_embeds_the_pinned_private_rules(self):
        expected = private_provider()
        self.assertEqual(len(expected['payload']), 133)
        self.assertIn('DOMAIN,router.asus.com', expected['payload'])
        self.assertIn('DOMAIN-SUFFIX,ts.net', expected['payload'])
        for name in ('StashKit.yaml', 'StashKit-Privacy.yaml', 'StashKit-Local.yaml'):
            with self.subTest(profile=name):
                profile = yaml.safe_load((ROOT / name).read_text())
                self.assertEqual(profile['rule-providers'][NAME], expected)
                self.assertEqual(profile['dns']['nameserver-policy']['rule-set:' + NAME], 'system')
                self.assertIn('rule-set:' + NAME, profile['dns']['fake-ip-filter'])
                self.assertNotIn('geosite:', (ROOT / name).read_text())

    def test_single_label_conversion_preserves_valid_dns_names(self):
        for value in ('a', 'nas', 'a-1', 'a-', '-a', '1a', 'nas.local', 'a' * 63,
                      'a' + '-' * 61 + 'b'):
            with self.subTest(value=value):
                self.assertEqual(bool(re.fullmatch(SOURCE_SINGLE_LABEL, value)),
                                 bool(re.fullmatch(SINGLE_LABEL, value)))
        self.assertNotIn(',', SINGLE_LABEL)

    def test_source_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT.parent) as tmp:
            root = Path(tmp)
            for name in ('build/private-domains-lock.json', 'build/private-domains.source.txt',
                         'rules/LICENSE.MIT-PRIVATE'):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / name).read_bytes())
            self.assertEqual(private_provider(root), private_provider())
            (root / 'build/private-domains.source.txt').write_text('example.com\n')
            with self.assertRaisesRegex(ValueError, 'SHA mismatch'):
                private_provider(root)


if __name__ == '__main__':
    unittest.main()
