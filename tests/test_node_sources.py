"""Exercise real-node expansion and failure boundaries without private subscriptions."""
import copy
import io
import os
import subprocess
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path
from unittest.mock import Mock, patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_loon_selection import build_flat_selection
from node_sources import (HTTPSRedirects, fetch_subscription, load_private_yaml,
                          resolve_node_sources)


def node(name, server='198.51.100.7'):
    return {'name': name, 'type': 'ss', 'server': server, 'port': 443,
            'cipher': 'aes-128-gcm', 'password': 'SECRET-PASSWORD'}


class NodeSourceTests(unittest.TestCase):
    def test_multiple_sources_keep_node_order_filters_and_benchmark_defaults(self):
        providers = {
            'arbitrary-provider-name': {'url': 'https://example.org/one?token=SECRET',
                                        'filter': 'HK', 'benchmark-timeout': 4,
                                        'headers': {'Accept': ['application/yaml', 'text/plain']}},
            'another-name': {'url': 'https://example.org/two'},
        }
        pools = [[node('HK-A'), node('US-A')], [node('JP-A')]]
        def fetcher(url, headers):
            if '/one?' in url:
                self.assertEqual(headers, {'Accept': 'application/yaml, text/plain'})
                return yaml.safe_dump({'proxies': pools[0]})
            return yaml.safe_dump({'proxies': pools[1]})
        local = [node('Local')]
        snapshot = copy.deepcopy((local, providers))
        resolved = resolve_node_sources(local, providers, fetcher=fetcher)
        self.assertEqual([n['name'] for n in resolved], ['Local', 'HK-A', 'JP-A'])
        self.assertEqual([n['benchmark-timeout'] for n in resolved], [5, 4, 5])
        self.assertTrue(all(n['benchmark-url'] == 'http://www.bing.com' for n in resolved))
        self.assertEqual((local, providers), snapshot)
        source = yaml.safe_load((ROOT / 'StashKit.yaml').read_text())
        output = build_flat_selection(source, providers, local, fetcher=fetcher)
        groups = {g['name']: g for g in output['proxy-groups']}
        self.assertEqual(groups['Fallback']['proxies'], ['Local', 'HK-A', 'JP-A'])
        self.assertEqual(groups['Proxy']['proxies'], ['Auto', 'Fallback', 'Local', 'HK-A', 'JP-A', 'REJECT'])
        self.assertEqual(groups['ChatGPT']['proxies'], ['Proxy', 'Auto', 'Fallback', 'Local', 'HK-A', 'JP-A'])
        self.assertNotIn('ALL', groups)
        self.assertNotIn('proxy-providers', output)
        self.assertNotIn('token=SECRET', yaml.safe_dump(output))
        self.assertFalse(any(set(g) & {'use', 'use-url', 'include-all'} for g in groups.values()))

    def test_local_provider_paths_are_relative_to_input_file(self):
        with tempfile.TemporaryDirectory(dir=ROOT.parent) as directory:
            base = Path(directory)
            (base / 'nodes.yaml').write_text(yaml.safe_dump({'proxies': [node('Local')]}))
            actual = resolve_node_sources(providers={'any': {'path': './nodes.yaml'}}, base_dir=base)
            self.assertEqual(actual[0]['name'], 'Local')

    def test_each_empty_or_failed_source_aborts_instead_of_returning_partial_nodes(self):
        for content, pattern in (({'proxies': []}, None), ({'rules': []}, None),
                                 ({'proxies': [node('US')]}, 'HK')):
            with self.subTest(content=content):
                provider = {'url': 'https://example.org/?SECRET', **({'filter': pattern} if pattern else {})}
                with self.assertRaises(ValueError):
                    resolve_node_sources([node('Working')], {'private': provider},
                                         fetcher=lambda *args: yaml.safe_dump(content))
        def fail(*args):
            raise OSError('SECRET URL and credentials')
        with self.assertRaises(ValueError) as error:
            resolve_node_sources([node('Working')], subscription_urls=['https://example.org/SECRET'], fetcher=fail)
        self.assertNotIn('SECRET', str(error.exception))

    def test_duplicate_node_names_are_deduplicated_only_for_identical_nodes(self):
        one = node('Same')
        result = resolve_node_sources([one, copy.deepcopy(one)])
        self.assertEqual(len(result), 1)
        with self.assertRaisesRegex(ValueError, 'Conflicting'):
            resolve_node_sources([one, node('Same', '198.51.100.8')])

    def test_invalid_nodes_and_builtin_substitutes_are_rejected(self):
        for invalid in ({**node('One'), 'port': True}, {**node('One'), 'type': 'direct'},
                        {**node('One'), 'port': 0}, {'name': 'Partial', 'type': 'ss'}):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    resolve_node_sources([invalid])
        with self.assertRaises(ValueError):
            resolve_node_sources()
        source = yaml.safe_load((ROOT / 'StashKit.yaml').read_text())
        for reserved in ('Auto', 'ALL', 'REJECT'):
            with self.assertRaisesRegex(ValueError, 'conflict'):
                build_flat_selection(source, nodes=[node(reserved)])

    def test_yaml_errors_never_echo_private_source_text(self):
        for content in ('proxies: [SECRET', 'SECRET: 1\nSECRET: 2\n', '!!python/object:SECRET {}'):
            with self.assertRaises(ValueError) as error:
                load_private_yaml(content)
            self.assertNotIn('SECRET', str(error.exception))

    def test_http_download_uses_verified_https_and_private_basic_auth(self):
        response = io.BytesIO(yaml.safe_dump({'proxies': [node('One')]}).encode())
        response.status = 200
        opener = Mock()
        opener.open.return_value = response
        with patch('node_sources.urllib.request.build_opener', return_value=opener):
            fetch_subscription('https://user:SECRET@example.org/sub?token=TOKEN')
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, 'https://example.org/sub?token=TOKEN')
        self.assertTrue(request.get_header('Authorization').startswith('Basic '))
        self.assertEqual(opener.open.call_args.kwargs['timeout'], 20)
        with self.assertRaises(ValueError):
            fetch_subscription('http://example.org/sub?SECRET')

    def test_redirect_downgrade_is_rejected_and_cross_host_headers_are_removed(self):
        handler = HTTPSRedirects()
        request = urllib.request.Request('https://example.org/sub', headers={'Authorization': 'SECRET',
                                                                          'X-Api-Key': 'SECRET'})
        redirected = handler.redirect_request(request, None, 302, 'Found', {}, 'https://cdn.example.org/sub')
        self.assertIsNone(redirected.get_header('Authorization'))
        self.assertIsNone(redirected.get_header('X-api-key'))
        with self.assertRaises(ValueError):
            handler.redirect_request(request, None, 302, 'Found', {}, 'http://example.org/sub')

    def test_cli_defaults_to_flat_and_writes_private_file_atomically(self):
        with tempfile.TemporaryDirectory(dir=ROOT.parent) as directory:
            source = Path(directory) / 'source.yaml'
            output = Path(directory) / 'result.yaml'
            source.write_text(yaml.safe_dump({'proxies': [node('One'), node('Two')]}))
            command = [sys.executable, str(ROOT / 'scripts/build_loon_selection.py'),
                       '--nodes-from', str(source), '--output', str(output)]
            success = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(success.returncode, 0, success.stderr)
            result = yaml.safe_load(output.read_text())
            self.assertEqual(len(result['proxy-groups']), 39)
            self.assertEqual(os.stat(output).st_mode & 0o777, 0o600)
            self.assertNotIn('SECRET', success.stdout + success.stderr)
            previous = output.read_bytes()
            source.write_text('proxies: [SECRET')
            failure = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(failure.returncode, 0)
            self.assertEqual(output.read_bytes(), previous)
            self.assertNotIn('SECRET', failure.stdout + failure.stderr)
            self.assertNotIn('Traceback', failure.stderr)

    def test_cli_refuses_to_overwrite_its_source(self):
        with tempfile.TemporaryDirectory(dir=ROOT.parent) as directory:
            source = Path(directory) / 'source.yaml'
            source.write_text(yaml.safe_dump({'proxies': [node('One')]}))
            previous = source.read_bytes()
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/build_loon_selection.py'),
                                     '--nodes-from', str(source), '--output', str(source)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(source.read_bytes(), previous)


if __name__ == '__main__':
    unittest.main()
