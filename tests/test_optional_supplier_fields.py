import sys
import json
from types import SimpleNamespace
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "_BUILD"))

import engine
import sync_drive
from drive_schema import LANGS, normalize_optional_fields, validate_product


def localized(value):
    return {language: value for language in LANGS}


def product():
    return {
        "folder": "28_OPTIONAL_FIELDS",
        "title": localized("Product"),
        "general": {key: localized(value) for key, value in {
            "typology": "Food", "shelf": "36 months", "packaging": "Jar",
            "labelling": "EU", "gmo": "None",
        }.items()} | {"ean": ""},
        "ingredients": {"ingredients": localized("Truffle"), "allergens": localized("None")},
        "storage": {"instructions": localized("Store"), "method": localized("Ready")},
        "nutrition": {key: "1 g" for key in ("energy", "fat", "sat", "carb", "sugar", "protein", "salt")},
    }


class OptionalSupplierFieldsTests(unittest.TestCase):
    def test_extraction_schema_allows_absent_optional_values_as_null(self):
        captured = {}

        def create_response(**kwargs):
            captured.update(kwargs)
            return SimpleNamespace(output_text=json.dumps({
                "nutrition": {"energy": "1 kJ / 1 kcal", "fat": "1 g", "sat": "0 g",
                              "carb": "1 g", "sugar": "0 g", "protein": "1 g", "salt": "0 g",
                              "fibre": None},
                "characteristics": {"chemical": None, "micro": None},
            }))

        client = SimpleNamespace(
            files=SimpleNamespace(create=lambda **_: SimpleNamespace(id="upload"), delete=lambda _: None),
            responses=SimpleNamespace(create=create_response),
        )
        extracted = sync_drive.extract(client, {"name": "supplier.pdf"}, b"%PDF test")
        schema = captured["text"]["format"]["schema"]
        self.assertEqual(schema["properties"]["nutrition"]["properties"]["fibre"]["type"], ["string", "null"])
        self.assertEqual(schema["properties"]["characteristics"]["properties"]["chemical"]["anyOf"][1], {"type": "null"})
        self.assertEqual(extracted["nutrition"]["fibre"], None)

    def test_missing_fibre_and_chemical_micro_are_valid_and_remain_omitted(self):
        source = product()
        self.assertEqual(validate_product(source), [])
        rendered = engine.render(source, "ITA", "06/06/2026")
        self.assertNotIn("Fibre</td>", rendered)
        self.assertNotIn("CARATTERISTICHE CHIMICHE E MICROBIOLOGICHE", rendered)

    def test_null_or_empty_optional_values_are_removed_but_partial_localization_is_invalid(self):
        source = product()
        source["nutrition"]["fibre"] = None
        source["characteristics"] = {
            "chemical": localized(""), "micro": None,
        }
        normalized = normalize_optional_fields(source)
        self.assertNotIn("fibre", normalized["nutrition"])
        self.assertNotIn("characteristics", normalized)
        self.assertEqual(validate_product(normalized), [])

        partial = product()
        partial["characteristics"] = {"chemical": localized(""), "micro": localized("Compliant")}
        partial["characteristics"]["chemical"]["DE"] = "pH geprüft"
        normalized_partial = normalize_optional_fields(partial)
        self.assertTrue(any("characteristics.chemical.ITA" in error for error in validate_product(normalized_partial)))

    def test_present_optional_values_are_preserved(self):
        source = product()
        source["nutrition"]["fibre"] = "0,0 g"
        source["characteristics"] = {"micro": localized("Specified")}
        normalized = normalize_optional_fields(source)
        self.assertEqual(normalized["nutrition"]["fibre"], "0,0 g")
        self.assertEqual(normalized["characteristics"]["micro"]["DE"], "Specified")
        self.assertEqual(validate_product(normalized), [])


if __name__ == "__main__":
    unittest.main()
