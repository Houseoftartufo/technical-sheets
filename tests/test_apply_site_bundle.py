import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_BUILD"))

from apply_site_bundle import apply_site_bundle
from i18n import LANGS


def make_product(root, folder, content):
    directory = root / folder
    directory.mkdir(parents=True, exist_ok=True)
    for language in LANGS:
        for extension in ("html", "pdf"):
            (directory / f"{folder}_{language}.{extension}").write_bytes(content)


class ApplySiteBundleTests(unittest.TestCase):
    def test_copies_exact_active_bundle_removes_only_owned_folder_and_preserves_unrelated_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            bundle = Path(temp) / "bundle"
            root.mkdir()
            bundle.mkdir()
            static = {"01_STATIC_ACTIVE", "02_STATIC_REMOVED"}
            make_product(root, "01_STATIC_ACTIVE", b"official bytes")
            make_product(root, "02_STATIC_REMOVED", b"remove after deploy")
            (root / "work").mkdir()
            (root / "work" / "keep.txt").write_text("do not stage", encoding="utf-8")
            make_product(bundle, "01_STATIC_ACTIVE", b"official bytes")
            make_product(bundle, "28_CARPACCIO_IN_OLIO", b"new validated bytes")
            (bundle / "index.html").write_text("28_CARPACCIO_IN_OLIO", encoding="utf-8")
            plan = {
                "active_products": {"01_STATIC_ACTIVE": {}, "28_CARPACCIO_IN_OLIO": {}},
                "next_manifest": {"products": {"source-1": {"folder": "01_STATIC_ACTIVE"},
                                                   "source-28": {"folder": "28_CARPACCIO_IN_OLIO"}}},
                "removed_folders": ["02_STATIC_REMOVED"],
            }

            result = apply_site_bundle(root, bundle, plan, static_folders=static)

            self.assertEqual(result["active_folders"], ["01_STATIC_ACTIVE", "28_CARPACCIO_IN_OLIO"])
            self.assertEqual(result["removed_folders"], ["02_STATIC_REMOVED"])
            self.assertEqual((root / "01_STATIC_ACTIVE" / "01_STATIC_ACTIVE_DE.pdf").read_bytes(), b"official bytes")
            self.assertEqual((root / "28_CARPACCIO_IN_OLIO" / "28_CARPACCIO_IN_OLIO_DE.pdf").read_bytes(), b"new validated bytes")
            self.assertFalse((root / "02_STATIC_REMOVED").exists())
            self.assertEqual((root / "work" / "keep.txt").read_text(encoding="utf-8"), "do not stage")
            self.assertEqual((root / "index.html").read_text(encoding="utf-8"), "28_CARPACCIO_IN_OLIO")

    def test_rejects_unexpected_bundle_folder_before_modifying_repository(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            bundle = Path(temp) / "bundle"
            root.mkdir()
            bundle.mkdir()
            make_product(bundle, "99_UNEXPECTED", b"unexpected")
            (root / "index.html").write_text("old index", encoding="utf-8")
            plan = {"active_products": {"28_EXPECTED": {}},
                    "next_manifest": {"products": {"source": {"folder": "28_EXPECTED"}}},
                    "removed_folders": []}

            with self.assertRaisesRegex(ValueError, "does not match active product list"):
                apply_site_bundle(root, bundle, plan, static_folders=set())

            self.assertEqual((root / "index.html").read_text(encoding="utf-8"), "old index")

    def test_rejects_removal_outside_product_folders(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            bundle = Path(temp) / "bundle"
            root.mkdir()
            bundle.mkdir()
            (root / "README.md").write_text("keep", encoding="utf-8")
            plan = {"active_products": {}, "next_manifest": {"products": {}},
                    "removed_folders": ["README.md"]}

            with self.assertRaisesRegex(ValueError, "Unsafe removed product folder"):
                apply_site_bundle(root, bundle, plan, static_folders=set())

            self.assertTrue((root / "README.md").exists())


if __name__ == "__main__":
    unittest.main()
