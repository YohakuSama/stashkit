"""The default must retain subscription updates and expose no helper selector."""
import copy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_loon_selection import build_loon_selection

PROVIDERS = {
    'arbitrary-primary': {
        'url': 'https://example.org/nodes?token=SECRET',
        'path': './providers/primary-cache.yaml',
        'interval': 1800,
        'headers': {'Authorization': 'Bearer SECRET', 'Accept': ['application/yaml', 'text/plain']},
        'filter': 'HK|JP',
        'benchmark-url': 'http://www.bing.com',
        'benchmark-timeout': 5,
    },
    'arbitrary-backup': {'url': 'https://example.org/backup', 'interval': 7200},
}


class NativeDefaultTests(unittest.TestCase):
    def assert_native(self, output, source_key, sources):
        groups = {g['name']: g for g in output['proxy-groups']}
        self.assertEqual(len(groups), 39)
        self.assertFalse({'ALL', 'Manual'} & set(groups))
        self.assertEqual(groups['Proxy']['proxies'], ['Auto', 'Fallback', 'REJECT'])
        self.assertEqual(groups['ChatGPT']['proxies'], ['Proxy', 'Auto', 'Fallback'])
        self.assertEqual(groups['Auto']['proxies'], [])
        self.assertEqual(groups['Fallback']['proxies'], [])
        for name, group in groups.items():
            self.assertNotIn('ALL', group['proxies'])
            self.assertNotIn('include-all', group)
            if name not in {'AdBlock', 'Final'}:
                self.assertEqual(group[source_key], sources)
            else:
                self.assertNotIn(source_key, group)
        return groups

    def test_api_default_binds_every_provider_directly_and_retains_refresh_metadata(self):
        for filename in ('StashKit.yaml', 'StashKit-Privacy.yaml', 'StashKit-Local.yaml'):
            template = yaml.safe_load((ROOT / filename).read_text())
            snapshot = copy.deepcopy((template, PROVIDERS))
            output = build_loon_selection(template, providers=PROVIDERS)
            self.assert_native(output, 'use', list(PROVIDERS))
            self.assertEqual(output['proxy-providers'], PROVIDERS)
            self.assertNotIn('proxies', output)
            self.assertEqual((template, PROVIDERS), snapshot)
            for field in ('dns', 'rules', 'rule-providers', 'mode', 'log-level'):
                self.assertEqual(output[field], template[field])

    def test_api_default_accepts_legacy_input_without_retaining_its_helper(self):
        template = yaml.safe_load((ROOT / 'StashKit-ALL.yaml').read_text())
        output = build_loon_selection(template, providers=PROVIDERS)
        self.assert_native(output, 'use', list(PROVIDERS))
        legacy = build_loon_selection(yaml.safe_load((ROOT / 'StashKit.yaml').read_text()),
                                      providers=PROVIDERS, layout='nested')
        self.assertIn('ALL', {g['name'] for g in legacy['proxy-groups']})
        self.assertEqual(len(legacy['proxy-groups']), 40)

    def test_cli_default_keeps_subscription_links_without_fetching_a_snapshot(self):
        # These deliberately unreachable HTTPS endpoints must remain references.
        urls = ['https://127.0.0.1:1/nodes?token=SECRET', 'https://127.0.0.1:1/backup']
        with tempfile.TemporaryDirectory(dir=ROOT.parent) as directory:
            source = Path(directory) / 'subscriptions.txt'
            output = Path(directory) / 'private.yaml'
            source.write_text('\n'.join(urls))
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/build_loon_selection.py'),
                                     '--subscription-file', str(source), '--output', str(output)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            profile = yaml.safe_load(output.read_text())
            self.assert_native(profile, 'use-url', urls)
            self.assertNotIn('proxies', profile)
            self.assertNotIn('proxy-providers', profile)
            self.assertNotIn('SECRET', result.stdout + result.stderr)

    def test_cli_provider_default_keeps_names_intervals_headers_and_cached_paths(self):
        with tempfile.TemporaryDirectory(dir=ROOT.parent) as directory:
            source = Path(directory) / 'providers.yaml'
            output = Path(directory) / 'private.yaml'
            source.write_text(yaml.safe_dump({'proxy-providers': PROVIDERS}, sort_keys=False))
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/build_loon_selection.py'),
                                     '--nodes-from', str(source), '--profile', 'privacy',
                                     '--output', str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            profile = yaml.safe_load(output.read_text())
            self.assert_native(profile, 'use', list(PROVIDERS))
            self.assertEqual(profile['proxy-providers'], PROVIDERS)
            self.assertTrue(profile['dns']['follow-rule'])
            self.assertNotIn('SECRET', result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
