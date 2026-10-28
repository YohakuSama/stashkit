"""Keep relative documentation links and copied attribution materials usable."""
import hashlib
import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


class DocumentationTests(unittest.TestCase):
    def test_relative_markdown_targets_exist(self):
        documents = [ROOT / "README.md", ROOT / "rules/README.md", *sorted((ROOT / "docs").glob("*.md"))]
        for document in documents:
            for link in re.findall(r"\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
                if urlsplit(link).scheme or link.startswith("#"):
                    continue
                path = (document.parent / link.split("#", 1)[0]).resolve()
                with self.subTest(document=document.name, link=link):
                    self.assertTrue(path.is_relative_to(ROOT), link)
                    self.assertTrue(path.exists(), link)

    def test_attribution_files_match_pinned_upstream(self):
        lock = json.loads((ROOT / "build/third-party-lock.json").read_text())
        source_lock = json.loads((ROOT / "build/source-lock.json").read_text())
        self.assertEqual(lock["commit"], source_lock["commit"])
        for item in lock["files"]:
            with self.subTest(path=item["path"]):
                content = (ROOT / item["path"]).read_bytes()
                self.assertEqual(hashlib.sha256(content).hexdigest(), item["sha256"])
                self.assertEqual(content, (ROOT / "upstream/loonkit" / item["upstream_path"]).read_bytes())


if __name__ == "__main__":
    unittest.main()
