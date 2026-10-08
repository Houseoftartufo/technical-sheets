import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_BUILD"))

from i18n import load_products_file


def imported_product():
    langs = ("ITA", "FR", "ENG", "NL", "DE")
    localized = lambda text: {lang: f"{text} {lang}" for lang in langs}
    return {
        "folder": "28_TEST_PRODUCT",
        "title": localized("Test"),
        "general": {
            "ean": "", "typology": localized("type"), "shelf": localized("shelf"),
            "packaging": localized("pack"), "labelling": localized("law"), "gmo": localized("none"),
        },
        "ingredients": {"ingredients": localized("ingredient"), "allergens": localized("none")},
        "storage": {"instructions": localized("store"), "method": localized("use")},
        "nutrition": {"energy": "1 kJ / 1 kcal"},
        "characteristics": {"chemical": localized(""), "micro": localized("")},
    }


class ImportedProductsTest(unittest.TestCase):
    def test_loader_accepts_fully_localized_supplier_product_without_static_translation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "supplier.json"
            path.write_text(json.dumps([imported_product()]), encoding="utf-8")

            loaded = load_products_file(path)

        self.assertEqual(loaded[0]["title"]["DE"], "Test DE")
        self.assertEqual(loaded[0]["ingredients"]["ingredients"]["DE"], "ingredient DE")


if __name__ == "__main__":
    unittest.main()
