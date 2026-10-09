import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_BUILD"))

from drive_bootstrap import load_baseline_mapping, seed_baseline_manifest
from drive_sync_state import OIL_CARPACCIO

ROOT = Path(__file__).resolve().parents[1]


class DriveBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.mapping = load_baseline_mapping(ROOT / "_BUILD" / "drive_baseline_mapping.json")["sources"]
        self.static_titles = {folder: {lang: f"Product {i} {lang}" for lang in ("ITA", "FR", "ENG", "NL", "DE")} for i, folder in enumerate([folder for folder in self.mapping.values() if folder != OIL_CARPACCIO["folder"]], start=1)}
        names = list(self.mapping)
        self.items = [{"id": f"source-{i}", "name": name, "mimeType": "application/pdf", "md5Checksum": f"md5-{i}", "size": str(i)} for i, name in enumerate(names)]

    def test_bootstrap_maps_27_legacy_sources_and_leaves_oil_carpaccio_for_first_generation(self):
        static_mapping = {name: folder for name, folder in self.mapping.items() if folder in self.static_titles}
        self.assertEqual(len(static_mapping), 27)
        result = seed_baseline_manifest(self.items, self.mapping, self.static_titles)
        self.assertEqual(len(result["manifest"]["products"]), 27)
        self.assertEqual(len(result["new_sources"]), 1)
        self.assertEqual(result["new_sources"][0]["name"], "Carpaccio di tartufo estivo - scheda tecnica.pdf")
        self.assertEqual(result["new_sources"][0]["folder"], OIL_CARPACCIO["folder"])
        self.assertEqual(result["manifest"]["legacy_folders"], [])

    def test_mapping_requires_every_expected_name_exactly_once(self):
        with self.assertRaisesRegex(ValueError, "missing source"):
            seed_baseline_manifest(self.items[:-1], self.mapping, self.static_titles)
        with self.assertRaisesRegex(ValueError, "unexpected source"):
            seed_baseline_manifest(self.items + [{"id": "extra", "name": "unknown.pdf", "mimeType": "application/pdf"}], self.mapping, self.static_titles)

    def test_bootstrap_recovers_after_a_partial_finalize_renamed_some_sources(self):
        partially_renamed = []
        for index, item in enumerate(self.items):
            folder = self.mapping[item["name"]]
            name = f"{folder}__{item['name']}" if index < 4 else item["name"]
            partially_renamed.append({**item, "name": name})
        result = seed_baseline_manifest(partially_renamed, self.mapping, self.static_titles)
        self.assertEqual(len(result["manifest"]["products"]), 27)
        self.assertEqual(result["new_sources"][0]["original_name"], "Carpaccio di tartufo estivo - scheda tecnica.pdf")
        self.assertEqual(result["new_sources"][0]["managed_name"], "28_CARPACCIO_DI_TARTUFO_ESTIVO_IN_OLIO__Carpaccio di tartufo estivo - scheda tecnica.pdf")

    def test_duplicate_source_names_and_product_folders_are_rejected(self):
        duplicate = self.items + [{**self.items[0], "id": "copy"}]
        with self.assertRaisesRegex(ValueError, "duplicate source name"):
            seed_baseline_manifest(duplicate, self.mapping, self.static_titles)
        duplicate_mapping = dict(self.mapping)
        names = list(duplicate_mapping)
        duplicate_mapping[names[-1]] = duplicate_mapping[names[0]]
        with self.assertRaisesRegex(ValueError, "duplicate mapped product folder"):
            seed_baseline_manifest(self.items, {"sources": duplicate_mapping}, self.static_titles)

    def test_missing_static_mapping_target_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "not present in static catalog"):
            seed_baseline_manifest(self.items, {"sources": self.mapping}, {folder: title for folder, title in list(self.static_titles.items())[1:]})


if __name__ == "__main__":
    unittest.main()
