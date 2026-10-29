"""Compare Stash choices with the independent, pinned LoonKit policy source."""
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / 'upstream/loonkit/LoonKit.lcf'
sys.path.insert(0, str(ROOT / 'scripts'))
from build_loon_selection import build_flat_selection
from validate_config import validate_profile

NODE = {'name': 'Example node', 'type': 'ss', 'server': '198.51.100.7',
        'port': 443, 'cipher': 'aes-128-gcm', 'password': 'test-only'}


def loon_groups():
    section = UPSTREAM.read_text().split('[Proxy Group]', 1)[1].split('[Remote Rule]', 1)[0]
    results = []
    for row in section.splitlines():
        if ' = ' not in row:
            continue
        name, body = row.split('=', 1)
        parts = [x.strip() for x in body.split(',img-url', 1)[0].split(',')]
        choices = [x for x in parts[1:] if '=' not in x]
        results.append((name.strip(), parts[0], choices))
    return results


class PolicyGroupParityTests(unittest.TestCase):
    def test_flat_output_expands_every_loon_filter_at_its_original_position(self):
        filters = {'ALL_Filter', 'Auto_Filter', 'Fallback_Filter'}
        expected = loon_groups()
        self.assertEqual(len(expected), 39)
        for filename in ('StashKit.yaml', 'StashKit-Privacy.yaml', 'StashKit-Local.yaml'):
            source = yaml.safe_load((ROOT / filename).read_text())
            result = build_flat_selection(source, nodes=[NODE])
            groups = result['proxy-groups']
            self.assertEqual([g['name'] for g in groups], [r[0] for r in expected])
            validate_profile(result)
            for group, (name, kind, choices) in zip(groups, expected):
                with self.subTest(profile=filename, group=name):
                    expanded = [NODE['name'] if child in filters else child for child in choices]
                    if name == 'Proxy':
                        expanded.append('REJECT')
                    self.assertEqual(group['type'], kind)
                    self.assertEqual(group['proxies'], expanded)
                    self.assertFalse(set(group) & {'use', 'use-url', 'include-all', 'filter'})
            for key in ('rules', 'rule-providers', 'dns'):
                self.assertEqual(result[key], source[key])

    def test_public_adapter_keeps_named_policies_separate_from_dynamic_nodes(self):
        expected = loon_groups()
        for filename in ('StashKit.yaml', 'StashKit-Privacy.yaml', 'StashKit-Local.yaml'):
            profile = yaml.safe_load((ROOT / filename).read_text())
            groups = {g['name']: g for g in profile['proxy-groups']}
            self.assertEqual(len(groups), 40)
            self.assertNotIn('proxy-providers', profile)
            for name, kind, choices in expected:
                with self.subTest(profile=filename, group=name):
                    translated = ['ALL' if c == 'ALL_Filter' else c for c in choices
                                  if c not in {'Auto_Filter', 'Fallback_Filter'}]
                    if name == 'Proxy':
                        translated.append('REJECT')
                    self.assertEqual(groups[name]['type'], kind)
                    self.assertEqual(groups[name]['proxies'], translated)
            for name in ('Auto', 'Fallback', 'ALL'):
                self.assertTrue(groups[name]['include-all'])
                self.assertEqual(groups[name]['filter'], '.*')
                self.assertEqual(groups[name]['proxies'], [])
            for name in set(groups) - {'Auto', 'Fallback', 'ALL'}:
                self.assertNotIn('include-all', groups[name])

    def test_original_timing_and_direct_defaults_are_preserved(self):
        source = yaml.safe_load((ROOT / 'StashKit.yaml').read_text())
        groups = {g['name']: g for g in build_flat_selection(source, nodes=[NODE])['proxy-groups']}
        self.assertEqual(groups['Auto']['interval'], 600)
        self.assertEqual(groups['Auto']['tolerance'], 60)
        self.assertEqual(groups['Fallback']['interval'], 900)
        for name in ('Apple', 'Microsoft', 'Bilibili', 'Line', 'Speedtest'):
            self.assertEqual(groups[name]['proxies'][0], 'DIRECT')
        self.assertEqual(groups['Steam']['proxies'][:4], ['Proxy', 'Auto', 'Fallback', 'DIRECT'])
        for name in ('Proxy', 'AI', 'ChatGPT', 'Gemini', 'Claude', 'Netflix'):
            self.assertNotIn('DIRECT', groups[name]['proxies'])
        self.assertEqual(groups['AdBlock']['proxies'], ['REJECT', 'DIRECT', 'Proxy'])
        self.assertEqual(groups['Final']['proxies'], ['Proxy', 'Auto', 'Fallback', 'DIRECT'])


if __name__ == '__main__':
    unittest.main()
