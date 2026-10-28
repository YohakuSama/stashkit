"""Bad inputs must fail before touching any committed output."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_rules import build


def digest(value):
    return hashlib.sha256(value).hexdigest()


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT.parent)
        self.addCleanup(self.temp.cleanup)
        self.kit = Path(self.temp.name) / "kit"
        self.source = Path(self.temp.name) / "source"
        (self.kit / "build").mkdir(parents=True)
        (self.kit / "rules").mkdir()
        (self.source / "build").mkdir(parents=True)
        (self.source / "rules").mkdir()
        self.input = self.source / "rules/Test.lsr"
        self.input.write_text("DOMAIN-SUFFIX,example.com\n", encoding="utf-8")
        profile = b"fixture profile\n"
        (self.source / "LoonKit.lcf").write_bytes(profile)
        manifest = {
            "label": "fixture", "profile_sha256": {"LoonKit.lcf": digest(profile)},
            "remote_subscription_count": 1, "remote_rule_count": 1,
            "runtime_resources": [{"path": "rules/Test.lsr", "sha256": digest(self.input.read_bytes()), "matcher_count": 1}],
        }
        frozen = json.dumps(manifest).encode()
        for root in (self.kit, self.source):
            (root / "build/release_manifest.json").write_bytes(frozen)
        commit = "a" * 40
        lock = {"schema_version": 1, "repository": "YohakuSama/loonkit", "commit": commit,
                "manifest_sha256": digest(frozen), "profile_sha256": digest(profile)}
        (self.kit / "build/source-lock.json").write_text(json.dumps(lock))
        adjustments = {"schema_version": 1, "source_commit": commit,
                       "expected_generated_rule_count": 1, "changes": []}
        (self.kit / "build/adjustments.json").write_text(json.dumps(adjustments))
        self.output = self.kit / "rules/Test.domain.txt"
        self.output.write_text("old committed bytes\n")

    def test_successful_build_and_repeat_are_identical(self):
        self.assertEqual(build(self.kit, self.source), (1, 1))
        self.assertEqual(self.output.read_text(), "# StashKit Test domain from LoonKit fixture\n+.example.com\n")
        self.assertEqual(build(self.kit, self.source, check=True), (1, 0))
        self.assertEqual(build(self.kit, self.source), (1, 0))

    def test_same_count_but_changed_input_is_rejected_without_writes(self):
        self.input.write_text("DOMAIN-SUFFIX,changed.example\n")
        with self.assertRaisesRegex(ValueError, "Source SHA mismatch"):
            build(self.kit, self.source)
        self.assertEqual(self.output.read_text(), "old committed bytes\n")

    def test_manifest_drift_is_rejected_without_writes(self):
        (self.source / "build/release_manifest.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "pinned snapshot"):
            build(self.kit, self.source)
        self.assertEqual(self.output.read_text(), "old committed bytes\n")

    def test_profile_drift_is_rejected_without_writes(self):
        (self.source / "LoonKit.lcf").write_text("changed profile")
        with self.assertRaisesRegex(ValueError, "profile SHA"):
            build(self.kit, self.source)
        self.assertEqual(self.output.read_text(), "old committed bytes\n")

    def test_obsolete_asset_is_rejected_before_writes(self):
        (self.kit / "rules/Obsolete.domain.txt").write_text("old\n")
        with self.assertRaisesRegex(ValueError, "Obsolete assets"):
            build(self.kit, self.source)
        self.assertEqual(self.output.read_text(), "old committed bytes\n")

    def test_check_does_not_write_or_accept_drift(self):
        with self.assertRaisesRegex(ValueError, "Rebuild differs"):
            build(self.kit, self.source, check=True)
        self.assertEqual(self.output.read_text(), "old committed bytes\n")

    def test_shipped_assets_reproduce(self):
        self.assertEqual(build(check=True), (54, 0))


if __name__ == "__main__":
    unittest.main()
