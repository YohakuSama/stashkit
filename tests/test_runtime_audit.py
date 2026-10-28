"""Mock Stash controller audit behavior; never contact a real device in CI."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from stash_runtime_audit import inspect


class RuntimeAuditTests(unittest.TestCase):
    def mock_get(self, mode="rule", count=54, selection="REJECT"):
        calls = []
        def getter(base, token, path):
            self.assertEqual(token, "secret-not-to-be-printed")
            calls.append(path)
            if path == "/version":
                return {"version": "fixture"}
            if path == "/configs":
                return {"mode": mode}
            if path == "/proxies":
                return {"proxies": {"Proxy": {"now": selection}}}
            if path == "/providers/rules":
                return {"providers": {f"provider-{i}": {} for i in range(count)}}
            if path == "/rules/count":
                return {"count": 196562}
            if path.startswith("/rules/match?"):
                return {"outbound": "DIRECT", "privateToken": "never-print"}
            if path == "/diagnosis/usedMemory":
                return {"memory": 1000000}
            raise AssertionError("Unexpected HTTP API request " + path)
        return getter, calls

    def test_expected_controller_get_only(self):
        getter, calls = self.mock_get()
        self.assertTrue(inspect("http://localhost:9090", "secret-not-to-be-printed", getter))
        self.assertEqual(len(calls), 11)
        self.assertTrue(all(path.startswith("/") for path in calls))

    def test_missing_providers_is_not_success(self):
        getter, _ = self.mock_get(count=53)
        self.assertFalse(inspect("http://localhost:9090", "secret-not-to-be-printed", getter))

    def test_non_rule_mode_is_not_success(self):
        getter, _ = self.mock_get(mode="direct")
        self.assertFalse(inspect("http://localhost:9090", "secret-not-to-be-printed", getter))


if __name__ == "__main__":
    unittest.main()
