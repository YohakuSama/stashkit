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


class RuntimeAuditTests(unittest.TestCase):
    def setUp(self):
        self.profile = yaml.safe_load((ROOT / "StashKit.yaml").read_text())
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


if __name__ == '__main__':
    unittest.main()
