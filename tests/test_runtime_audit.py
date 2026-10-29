"""Reject unloaded rules and unsafe nested selections using controller fixtures."""
import contextlib
import copy
import io
import sys
import unittest
import urllib.parse
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from stash_runtime_audit import SENTINELS, expected_counts, inspect
from build_loon_selection import build_loon_selection


class RuntimeAuditTests(unittest.TestCase):
    def setUp(self):
        self.template = yaml.safe_load((ROOT / "StashKit.yaml").read_text())
        self.profile = build_loon_selection(self.template, providers={
            "runtime-provider": {"url": "https://example.org/nodes", "interval": 3600}})
        self.calls = []
        counts = expected_counts(self.profile)
        self.responses = {
            "/version": {"version": "fixture"},
            "/configs": {"mode": "rule"},
            "/proxies": {"proxies": {
                "Proxy": {"type": "Selector", "now": "Auto"},
                "Auto": {"type": "URLTest", "now": "private-node-name"},
                "private-node-name": {"type": "Shadowsocks"},
                "ChatGPT": {"type": "Selector", "now": "Proxy"},
                "GitHub": {"type": "Selector", "now": "Proxy"},
                "AdBlock": {"type": "Selector", "now": "REJECT"},
            }},
            "/providers/rules": {"providers": {name: {"ruleCount": count} for name, count in counts.items()}},
            "/rules/count": {"count": sum(counts[row.split(',')[1]] if row.startswith('RULE-SET,') else 1
                                           for row in self.profile["rules"])},
            "/diagnosis/usedMemory": {"memory": 1000000},
        }
        loaded = self.responses['/proxies']['proxies']
        for group in self.profile['proxy-groups']:
            kind = {'select': 'Selector', 'url-test': 'URLTest', 'fallback': 'Fallback'}[group['type']]
            members = group['proxies'][:] + (['private-node-name'] if group.get('use') else [])
            loaded[group['name']] = {'type': kind, 'all': members, 'now': members[0]}
        for target, kind, payload, policy in SENTINELS:
            self.responses[self.match_path(target)] = {
                "rule": {"type": kind, "payload": payload},
                "outbound": {"DIRECT": "DIRECT", "AdBlock": "REJECT"}.get(policy, "private-node-name"),
                "privateToken": "never-print",
            }

    @staticmethod
    def match_path(target):
        return "/rules/match?" + urllib.parse.urlencode({"target": target, "resolve": "false"})

    def getter(self, base, token, path):
        self.assertEqual(token, "secret-not-to-be-printed")
        self.calls.append(path)
        return copy.deepcopy(self.responses[path])

    def run_audit(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = inspect("http://localhost:9090", "secret-not-to-be-printed", self.getter, self.profile)
        log = stdout.getvalue() + stderr.getvalue()
        for sensitive in ("secret-not-to-be-printed", "never-print", "private-node-name"):
            self.assertNotIn(sensitive, log)
        return result

    def test_valid_controller_response_and_get_only(self):
        self.assertTrue(self.run_audit())
        self.assertEqual(len(self.calls), 6 + len(SENTINELS))
        self.assertTrue(all(path.startswith('/') for path in self.calls))

    def test_missing_or_wrong_provider_names_fail(self):
        providers = self.responses['/providers/rules']['providers']
        providers['wrong-name'] = providers.pop('ChatGPT-domain')
        self.assertFalse(self.run_audit())

    def test_empty_provider_with_correct_name_fails(self):
        self.responses['/providers/rules']['providers']['ChatGPT-domain'] = {}
        self.assertFalse(self.run_audit())

    def test_wrong_entry_count_or_load_failure_fails(self):
        original = copy.deepcopy(self.responses['/providers/rules'])
        for bad in ({'ruleCount': 0}, {'ruleCount': 19, 'error': 'private-node-name'},
                    {'ruleCount': 19, 'status': 'failed'}):
            with self.subTest(provider=bad):
                self.responses['/providers/rules'] = copy.deepcopy(original)
                self.responses['/providers/rules']['providers']['ChatGPT-domain'] = bad
                self.assertFalse(self.run_audit())

    def test_zero_total_rules_fails(self):
        self.responses['/rules/count']['count'] = 0
        self.assertFalse(self.run_audit())

    def test_direct_substitution_inside_auto_fails(self):
        self.responses['/proxies']['proxies']['Auto']['now'] = 'DIRECT'
        self.assertFalse(self.run_audit())

    def test_reject_default_is_not_service_acceptance(self):
        self.responses['/proxies']['proxies']['Proxy']['now'] = 'REJECT'
        self.assertFalse(self.run_audit())

    def test_nested_selection_cycle_fails(self):
        self.responses['/proxies']['proxies']['Auto']['now'] = 'Proxy'
        self.assertFalse(self.run_audit())

    def test_missing_nested_selection_fails(self):
        del self.responses['/proxies']['proxies']['Auto']['now']
        self.assertFalse(self.run_audit())

    def test_all_targets_direct_is_not_success(self):
        for target, *_ in SENTINELS:
            self.responses[self.match_path(target)]['outbound'] = 'DIRECT'
        self.assertFalse(self.run_audit())

    def test_wrong_rule_even_with_correct_outbound_fails(self):
        self.responses[self.match_path('api.openai.com')]['rule'] = {'type': 'MATCH', 'payload': ''}
        self.assertFalse(self.run_audit())

    def test_missing_routing_evidence_fails(self):
        self.responses[self.match_path('api.openai.com')] = {}
        self.assertFalse(self.run_audit())

    def test_flat_rule_fields_are_supported(self):
        d = self.responses[self.match_path('api.openai.com')]
        rule = d.pop('rule')
        d.update(ruleType=rule['type'], rulePayload=rule['payload'])
        self.assertTrue(self.run_audit())

    def test_non_rule_mode_fails(self):
        self.responses['/configs']['mode'] = 'direct'
        self.assertFalse(self.run_audit())

    def test_missing_auto_choice_fails_even_when_proxy_has_a_working_node(self):
        groups = self.responses['/proxies']['proxies']
        groups['Proxy']['all'] = ['private-node-name']
        groups['Proxy']['now'] = 'private-node-name'
        self.assertFalse(self.run_audit())

    def test_unused_fallback_empty_provider_substitution_fails(self):
        groups = self.responses['/proxies']['proxies']
        groups['Fallback']['all'] = ['DIRECT']
        groups['Fallback']['now'] = 'DIRECT'
        self.assertFalse(self.run_audit())

    def test_missing_service_group_or_wrong_type_fails(self):
        groups = self.responses['/proxies']['proxies']
        del groups['Netflix']
        groups['Apple']['type'] = 'URLTest'
        self.assertFalse(self.run_audit())

    def test_reject_or_nested_group_in_node_pool_fails(self):
        groups = self.responses['/proxies']['proxies']
        for substitute in ('REJECT', 'ChatGPT'):
            with self.subTest(substitute=substitute):
                groups['Fallback']['all'] = ['private-node-name', substitute]
                self.assertFalse(self.run_audit())

    def test_mismatched_node_pools_fail(self):
        groups = self.responses['/proxies']['proxies']
        groups['second-private-node'] = {'type': 'Shadowsocks'}
        groups['Fallback']['all'].append('second-private-node')
        self.assertFalse(self.run_audit())

    def test_unexpected_direct_choice_in_overseas_service_fails(self):
        self.responses['/proxies']['proxies']['ChatGPT']['all'].append('DIRECT')
        self.assertFalse(self.run_audit())

    def test_business_selector_missing_provider_nodes_is_not_success(self):
        self.responses['/proxies']['proxies']['ChatGPT']['all'].remove('private-node-name')
        self.assertFalse(self.run_audit())

    def test_provider_update_is_checked_without_regenerating_the_profile(self):
        snapshot = copy.deepcopy(self.profile)
        loaded = self.responses['/proxies']['proxies']
        loaded['updated-private-node'] = {'type': 'Shadowsocks'}
        for group in self.profile['proxy-groups']:
            if group.get('use'):
                loaded[group['name']]['all'].append('updated-private-node')
        self.assertTrue(self.run_audit())
        self.assertEqual(self.profile, snapshot)
        loaded['Proxy']['all'].remove('updated-private-node')
        self.assertFalse(self.run_audit())

    def test_use_url_nodes_receive_the_same_runtime_checks(self):
        self.profile = build_loon_selection(self.template,
                                            subscription_urls=['https://example.org/nodes'])
        self.assertTrue(self.run_audit())
        self.responses['/proxies']['proxies']['Netflix']['all'].remove('private-node-name')
        self.assertFalse(self.run_audit())

    def test_unreplaced_public_provider_is_not_an_accepted_private_configuration(self):
        self.profile = self.template
        self.assertFalse(self.run_audit())

    def test_placeholder_is_rejected_even_when_controller_reports_working_nodes(self):
        self.profile["proxy-providers"]["Airport"]["url"] = (
            "https://example.invalid/REPLACE-WITH-YOUR-CLASH-SUBSCRIPTION")
        self.assertFalse(self.run_audit())

    def test_extra_helper_in_native_runtime_fails(self):
        self.responses['/proxies']['proxies']['ALL'] = {
            'type': 'Selector', 'all': ['private-node-name'], 'now': 'private-node-name'}
        self.assertFalse(self.run_audit())


if __name__ == '__main__':
    unittest.main()
