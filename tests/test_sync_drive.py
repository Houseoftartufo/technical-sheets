import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_BUILD"))

import sync_drive
from drive_schema import LANGS, validate_product


class Request:
    def __init__(self, value):
        self.value = value

    def execute(self):
        return self.value


class FakeFiles:
    def __init__(self, drive):
        self.drive = drive

    def get(self, fileId, **kwargs):
        return Request(next(item for item in self.drive.items if item["id"] == fileId))

    def list(self, q, **kwargs):
        self.drive.queries.append((q, kwargs))
        parent = q.split("'")[1]
        name = None
        if "name = '" in q:
            name = q.split("name = '", 1)[1].split("'", 1)[0]
        mime = None
        if "mimeType = '" in q:
            mime = q.split("mimeType = '", 1)[1].split("'", 1)[0]
        found = [item for item in self.drive.items
                 if parent in item.get("parents", [])
                 and not item.get("trashed")
                 and (name is None or item["name"] == name)
                 and (mime is None or item["mimeType"] == mime)]
        return Request({"files": found})

    def create(self, body, **kwargs):
        item = {"id": "created-folder", **body}
        self.drive.items.append(item)
        self.drive.mutations += 1
        return Request(item)

    def update(self, *args, **kwargs):
        self.drive.mutations += 1
        return Request({})


class FakeDrive:
    def __init__(self, items):
        self.items = items
        self.queries = []
        self.mutations = 0

    def files(self):
        return FakeFiles(self)


def valid_product(folder="28_NEW"):
    localized = {language: f"Product {language}" for language in LANGS}
    return {
        "folder": folder,
        "title": localized.copy(),
        "general": {
            "ean": "",
            "typology": localized.copy(),
            "shelf": localized.copy(),
            "packaging": localized.copy(),
            "labelling": localized.copy(),
            "gmo": localized.copy(),
        },
        "ingredients": {"ingredients": localized.copy(), "allergens": localized.copy()},
        "storage": {"instructions": localized.copy(), "method": localized.copy()},
        "nutrition": {key: "0 g" for key in ("energy", "fat", "sat", "carb", "sugar", "protein", "salt", "fibre")},
        "characteristics": {"chemical": localized.copy(), "micro": localized.copy()},
    }


class SyncDriveTests(unittest.TestCase):
    def test_processed_folder_is_created_as_sibling_and_reused(self):
        drive = FakeDrive([{
            "id": "intake", "name": "DA_ELABORARE", "mimeType": "application/vnd.google-apps.folder",
            "parents": ["shared-root"],
        }])

        created = sync_drive.ensure_processed_folder(drive, "intake")
        found = sync_drive.ensure_processed_folder(drive, "intake")

        self.assertEqual(created["id"], "created-folder")
        self.assertEqual(found["id"], created["id"])
        self.assertEqual(drive.items[-1]["parents"], ["shared-root"])
        self.assertEqual(drive.mutations, 1)

    def test_prepare_processes_only_direct_children_of_intake_and_active_folders(self):
        pending = {"id": "pending", "name": "new.pdf", "mimeType": "application/pdf", "md5Checksum": "new", "parents": ["intake"]}
        active = {"id": "active", "name": "active.pdf", "mimeType": "application/pdf", "md5Checksum": "active", "parents": ["processed"]}
        outside = {"id": "outside", "name": "outside.pdf", "mimeType": "application/pdf", "md5Checksum": "other", "parents": ["elsewhere"]}
        drive = FakeDrive([pending, active, outside])
        manifest = {"version": 2, "products": {
            "active": {"fingerprint": sync_drive.source_fingerprint(active), "folder": "29_ACTIVE", "title": {"ITA": "Active"}}
        }}
        with tempfile.TemporaryDirectory() as temp, \
             patch.object(sync_drive, "download", return_value=b"pdf"), \
             patch.object(sync_drive, "extract", return_value=valid_product()) as extract:
            plan = sync_drive.prepare(drive, "intake", "processed", manifest, object(), run_dir=Path(temp))

            self.assertEqual([item["id"] for item in plan["changed_pending"]], ["pending"])
            self.assertEqual(plan["unchanged"], ["active"])
            self.assertEqual(plan["move_source_ids"], ["pending"])
            self.assertNotIn("outside", json.dumps(plan))
            extract.assert_called_once()
            saved = json.loads((Path(temp) / "drive_sync_plan.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["move_source_ids"], ["pending"])
        self.assertEqual(drive.mutations, 0)
        self.assertEqual(pending["parents"], ["intake"])

    def test_incomplete_required_translation_blocks_but_blank_ean_is_allowed(self):
        product = valid_product()
        product["title"]["DE"] = ""
        errors = validate_product(product)
        self.assertTrue(any("title" in error and "DE" in error for error in errors))

        product = valid_product()
        self.assertEqual(product["general"]["ean"], "")
        self.assertEqual(validate_product(product), [])

    def test_prepare_keeps_intake_file_and_reports_validation_failure_without_writing_manifest(self):
        pending = {"id": "pending", "name": "new.pdf", "mimeType": "application/pdf", "md5Checksum": "x", "parents": ["intake"]}
        drive = FakeDrive([pending])
        product = valid_product()
        product["ingredients"]["allergens"]["FR"] = ""
        manifest = {"version": 2, "products": {}}
        with tempfile.TemporaryDirectory() as temp, \
             patch.object(sync_drive, "download", return_value=b"pdf"), \
             patch.object(sync_drive, "extract", return_value=product):
            plan = sync_drive.prepare(drive, "intake", "processed", manifest, object(), run_dir=Path(temp))

        self.assertEqual(plan["status"], "blocked")
        self.assertEqual(plan["removed_folders"], [])
        self.assertTrue(plan["errors"])
        self.assertEqual(pending["parents"], ["intake"])
        self.assertEqual(manifest, {"version": 2, "products": {}})
        self.assertEqual(drive.mutations, 0)

    def test_folder_collision_blocks_instead_of_silently_creating_duplicate_product(self):
        folder = "01_ACETO_BALSAMICO_SPRAY"
        source = {"id": "pending", "name": "new.pdf", "mimeType": "application/pdf", "md5Checksum": "x", "parents": ["intake"]}
        drive = FakeDrive([source])
        with tempfile.TemporaryDirectory() as temp, \
             patch.object(sync_drive, "download", return_value=b"pdf"), \
             patch.object(sync_drive, "extract", return_value=valid_product(folder)):
            plan = sync_drive.prepare(drive, "intake", "processed", {"version": 2, "products": {}}, object(), run_dir=Path(temp))

        self.assertEqual(plan["status"], "blocked")
        self.assertTrue(any("collision" in error.lower() for error in plan["errors"][0]["errors"]))
        self.assertEqual(source["parents"], ["intake"])
        self.assertEqual(drive.mutations, 0)

    def test_unsupported_source_blocks_without_treating_it_as_a_deletion(self):
        unsupported = {"id": "legacy", "name": "notes.txt", "mimeType": "text/plain", "parents": ["processed"]}
        drive = FakeDrive([unsupported])
        manifest = {"version": 2, "products": {"legacy": {"folder": "28_KEEP", "fingerprint": "old"}}}
        with tempfile.TemporaryDirectory() as temp:
            plan = sync_drive.prepare(drive, "intake", "processed", manifest, object(), run_dir=Path(temp))

        self.assertEqual(plan["status"], "blocked")
        self.assertEqual(plan["removed_source_ids"], [])
        self.assertEqual(plan["removed_folders"], [])
        self.assertEqual(drive.mutations, 0)


if __name__ == "__main__":
    unittest.main()
