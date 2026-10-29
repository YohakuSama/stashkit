"""Candidate checks must retain the public host and reject unsafe refs/paths."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_remote import PREFIX, published_url


class RemoteURLTests(unittest.TestCase):
    def test_production_url_is_immutable(self):
        self.assertIn("f4feec81dfc9bde9824d297b6959fa977d5dc39b", PREFIX)
        self.assertNotIn("/main/", PREFIX)
        url = PREFIX + "ChatGPT.domain.txt"
        self.assertEqual(published_url({"url": url}), (url, "ChatGPT.domain.txt"))

    def test_candidate_uses_pinned_revision_and_same_asset(self):
        ref = "a" * 40
        url, name = published_url({"url": PREFIX + "ChatGPT.domain.txt"}, ref)
        self.assertEqual(url, f"https://raw.githubusercontent.com/YohakuSama/stashkit/{ref}/rules/ChatGPT.domain.txt")
        self.assertEqual(name, "ChatGPT.domain.txt")

    def test_unsafe_refs_are_rejected(self):
        for ref in ("main", "../main", "a" * 39, "a" * 40 + "/extra"):
            with self.subTest(ref=ref):
                with self.assertRaises(ValueError):
                    published_url({"url": PREFIX + "ChatGPT.domain.txt"}, ref)

    def test_foreign_host_and_unsafe_filename_are_rejected(self):
        for url in ("https://example.com/rules.txt", PREFIX + "../private.txt",
                    PREFIX + "file.txt?token=bad", PREFIX + "subdir/file.txt"):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    published_url({"url": url})


if __name__ == "__main__":
    unittest.main()
