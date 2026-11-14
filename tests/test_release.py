"""Validate release metadata and prevent accidental rule snapshot repinning."""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_profiles import local_profile
from release_meta import (PROFILE_VERSION, RULES_VERSION, RULES_REF,
                          RULES_PATH_PREFIX, RULES_URL_PREFIX, archive_name, load_lock)


class ReleaseMetadataTests(unittest.TestCase):
    def test_versioned_profiles_and_readme_agree_with_release_lock(self):
        names = (("StashKit.yaml", f"# StashKit {PROFILE_VERSION}"),)
        for name, header in names:
            with self.subTest(file=name):
                content = (ROOT / name).read_text(encoding="utf-8")
                self.assertEqual(content.splitlines()[0], header)
        self.assertIn(f"当前配置：**{PROFILE_VERSION}**",
                      (ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertTrue((ROOT / "docs" / f"RELEASE_NOTES_{PROFILE_VERSION}.md").is_file())
        self.assertEqual(archive_name(), f"StashKit-{PROFILE_VERSION}-offline.zip")
        self.assertFalse((ROOT / "StashKit-SelfHosted.yaml").exists())

    def test_existing_immutable_rule_snapshot_is_reused(self):
        standard = (ROOT / "StashKit.yaml").read_text(encoding="utf-8")
        local = local_profile(standard)
        self.assertRegex(RULES_VERSION, r"^v[0-9]+\.[0-9]+\.[0-9]+$")
        self.assertTrue(re.fullmatch(r"[0-9a-f]{40}", RULES_REF))
        self.assertEqual(standard.count(RULES_URL_PREFIX), 54)
        self.assertEqual(standard.count(RULES_PATH_PREFIX), 54)
        self.assertEqual(local.count(RULES_PATH_PREFIX), 54)
        self.assertNotIn("url: https://raw.githubusercontent.com/", local)
        self.assertIn("/fd6627fc33eef9cf1e93b001a2327c47b0993133/rules/extra/Crypto.v7.0.13.domain.txt", standard)
        self.assertIn("./rules/v0.1.18/Crypto.v7.0.13.domain.txt", local)

    def test_malformed_release_locks_are_rejected(self):
        valid = load_lock()
        changes = (
            {**valid, "profile_version": "latest"},
            {**valid, "rules_version": "../rules"},
            {**valid, "source_ref": "main"},
            {**valid, "unexpected": "value"},
            {k: v for k, v in valid.items() if k != "rules_version"},
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "release-lock.json"
            for data in changes:
                with self.subTest(data=data):
                    path.write_text(json.dumps(data), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        load_lock(path)

    def test_release_job_runs_after_verification_and_has_scoped_write(self):
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("  release:\n", workflow)
        self.assertIn("    needs: verify\n", workflow)
        self.assertIn("    if: github.event_name == 'push' && github.ref == 'refs/heads/main'\n",
                      workflow)
        self.assertIn("    permissions:\n      contents: write\n", workflow)
        self.assertIn("gh release create", workflow)
        release_job = workflow.split("\n  release:\n", 1)[1]
        self.assertIn("python-version: '3.12'", release_job)
        self.assertIn("python -m pip install -r requirements-dev.txt", release_job)


if __name__ == "__main__":
    unittest.main()
