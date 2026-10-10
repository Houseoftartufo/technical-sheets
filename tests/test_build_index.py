import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "_BUILD" / "build_index.py"
sys.path.insert(0, str(ROOT / "_BUILD"))
from build_index import load_static_titles


class BuildIndexTests(unittest.TestCase):
    def run_builder(self, *args):
        result = subprocess.run(
            [sys.executable, str(BUILDER), *map(str, args)],
            capture_output=True, text=True,
        )
        if result.returncode:
            self.fail(result.stderr)
        return result

    def make_site_root(self, root):
        root.mkdir(parents=True)
        for folder in load_static_titles():
            (root / folder).mkdir()

    def test_default_index_still_contains_only_the_27_static_products(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "index.html"
            self.run_builder("--output", output)

            html = output.read_text(encoding="utf-8")

        self.assertEqual(len(re.findall(r'<div class="card(?: |")', html)), 27)
        self.assertNotIn("28_TEST", html)

    def test_static_products_can_be_filtered_by_authoritative_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            site = Path(temp) / "site"
            self.make_site_root(site)
            all_folders = sorted(path.name for path in site.iterdir() if path.is_dir())
            removed = all_folders[0]
            (site / removed).rmdir()
            active = Path(temp) / "active-static.json"
            active.write_text(json.dumps([folder for folder in all_folders if folder != removed]), encoding="utf-8")
            output = site / "index.html"
            self.run_builder("--output", output, "--site-root", site, "--static-products", active)
            html = output.read_text(encoding="utf-8")

        self.assertEqual(len(re.findall(r'<div class="card(?: |")', html)), 26)
        self.assertNotIn(removed, html)

    def test_dynamic_metadata_adds_searchable_product_with_five_language_links(self):
        titles = {
            "28_TEST": {
                "ITA": "Tartufo di prova",
                "FR": "Truffe de test",
                "ENG": "Test truffle",
                "NL": "Testtruffel",
                "DE": "Weißer Testtrüffel",
            }
        }
        with tempfile.TemporaryDirectory() as temp:
            site = Path(temp) / "site"
            self.make_site_root(site)
            product = site / "28_TEST"
            product.mkdir(parents=True)
            (product / "28_TEST_ITA.pdf").write_bytes(b"%PDF-1.4")
            metadata = Path(temp) / "products.json"
            metadata.write_text(json.dumps(titles, ensure_ascii=False), encoding="utf-8")
            output = site / "index.html"
            self.run_builder("--output", output, "--site-root", site, "--dynamic-products", metadata)

            html = output.read_text(encoding="utf-8")

        self.assertEqual(len(re.findall(r'<div class="card(?: |")', html)), 28)
        for language in ("ITA", "FR", "ENG", "NL", "DE"):
            self.assertIn(f'href="28_TEST/28_TEST_{language}.pdf"', html)
        self.assertIn("Tartufo di prova", html)
        self.assertIn("Truffe de test", html)
        self.assertIn("Test truffle", html)
        self.assertIn("Testtruffel", html)
        self.assertIn("Weißer Testtrüffel", html)

    def test_unlisted_dynamic_folder_is_excluded_when_removed_from_active_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            site = Path(temp) / "site"
            self.make_site_root(site)
            (site / "28_REMOVED").mkdir(parents=True)
            metadata = Path(temp) / "products.json"
            metadata.write_text("{}", encoding="utf-8")
            output = site / "index.html"
            self.run_builder("--output", output, "--site-root", site, "--dynamic-products", metadata)

            html = output.read_text(encoding="utf-8")

        self.assertEqual(len(re.findall(r'<div class="card(?: |")', html)), 27)
        self.assertNotIn("28_REMOVED", html)


if __name__ == "__main__":
    unittest.main()
