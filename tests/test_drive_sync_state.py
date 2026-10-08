import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_BUILD"))

from drive_sync_state import (canonicalize_product, source_fingerprint, unchanged_source_ids,
                               product_manifest_entry, removed_product_folders, load_manifest, resolve_output_folder)


class Request:
    def __init__(self, value):
        self.value = value
    def execute(self):
        return self.value


class Files:
    def __init__(self, drive):
        self.drive = drive
    def list(self, q, **kwargs):
        if "mimeType = 'application/vnd.google-apps.folder'" in q:
            import re
            match = re.search(r"name = '([^']+)'", q)
            found = [item for item in self.drive.items if match and item["name"] == match.group(1)]
            return Request({"files": found})
        if "in parents" in q:
            parent = q.split("'")[1]
            found = next((item["children"] for item in self.drive.items if item["id"] == parent), [])
            return Request({"files": found})
        return Request({"files": []})
    def update(self, fileId, body, **kwargs):
        item = next(item for item in self.drive.items if item["id"] == fileId)
        item.update(body)
        return Request(item)
    def create(self, body, **kwargs):
        self.drive.created += 1
        item = {"id": "new-folder", "name": body["name"], "children": []}
        self.drive.items.append(item)
        return Request({"id": item["id"]})


class FakeDrive:
    def __init__(self, items):
        self.items = items
        self.created = 0
    def files(self):
        return Files(self)


class DriveSyncStateTest(unittest.TestCase):
    def test_carpaccio_in_oil_is_catalog_product_28_not_water_product_06(self):
        product = {"folder": "CARPACCIO", "title": {"ITA": "Carpaccio di tartufo estivo"}}
        result = canonicalize_product(product, "Carpaccio di tartufo estivo - scheda tecnica.pdf")
        self.assertEqual(result["folder"], "28_CARPACCIO_DI_TARTUFO_ESTIVO_IN_OLIO")
        self.assertEqual(result["title"]["ITA"], "Carpaccio di tartufo estivo in olio")
        self.assertEqual(result["title"]["FR"], "Carpaccio de truffe d’été à l’huile")
        self.assertEqual(product["folder"], "CARPACCIO")

    def test_source_with_explicit_water_is_not_reclassified_as_oil(self):
        product = {"folder": "06_CARPACCIO_DI_TARTUFO_IN_ACQUA", "title": {"ITA": "Carpaccio in acqua"}}
        result = canonicalize_product(product, "Carpaccio di tartufo in acqua.pdf")
        self.assertEqual(result["folder"], "06_CARPACCIO_DI_TARTUFO_IN_ACQUA")

    def test_failed_empty_carpaccio_folder_is_reused_without_creating_orphan_folder(self):
        from publish_drive import ensure_product_folder
        drive = FakeDrive([{"id": "empty", "name": "CARPACCIO_DI_TARTUFO_ESTIVO", "children": []}])
        result = ensure_product_folder(drive, "28_CARPACCIO_DI_TARTUFO_ESTIVO_IN_OLIO")
        self.assertEqual(result, "empty")
        self.assertEqual(drive.items[0]["name"], "28_CARPACCIO_DI_TARTUFO_ESTIVO_IN_OLIO")
        self.assertEqual(drive.created, 0)

    def test_nonempty_legacy_folder_is_preserved_and_new_identity_is_created(self):
        from publish_drive import ensure_product_folder
        drive = FakeDrive([{"id": "occupied", "name": "CARPACCIO_DI_TARTUFO_ESTIVO", "children": [{"id": "old-sheet"}]}])
        result = ensure_product_folder(drive, "28_CARPACCIO_DI_TARTUFO_ESTIVO_IN_OLIO")
        self.assertEqual(result, "new-folder")
        self.assertEqual(drive.items[0]["name"], "CARPACCIO_DI_TARTUFO_ESTIVO")
        self.assertEqual(drive.created, 1)

    def test_two_supplier_sheets_cannot_silently_share_one_product_folder(self):
        imported = {}
        first = {"folder": "28_CARPACCIO_DI_TARTUFO_ESTIVO_IN_OLIO"}
        folder, error = resolve_output_folder(first, set(), imported)
        self.assertEqual(folder, "28_CARPACCIO_DI_TARTUFO_ESTIVO_IN_OLIO")
        self.assertIsNone(error)
        imported[folder] = first

        second = {"folder": "28_CARPACCIO_DI_TARTUFO_ESTIVO_IN_OLIO"}
        folder, error = resolve_output_folder(second, set(), imported)
        self.assertIsNone(folder)
        self.assertIn("Multiple supplier files", error)
        self.assertEqual(second["folder"], "28_CARPACCIO_DI_TARTUFO_ESTIVO_IN_OLIO")

    def test_new_supplier_duplicate_gets_separate_folder_from_unchanged_source(self):
        product = {"folder": "28_CARPACCIO_DI_TARTUFO_ESTIVO_IN_OLIO"}
        folder, error = resolve_output_folder(
            product, set(), {}, {"28_CARPACCIO_DI_TARTUFO_ESTIVO_IN_OLIO"}
        )
        self.assertIsNone(error)
        self.assertEqual(folder, "DUPLICATE_28_CARPACCIO_DI_TARTUFO_ESTIVO_IN_OLIO")
        self.assertEqual(product["duplicate_of"], "28_CARPACCIO_DI_TARTUFO_ESTIVO_IN_OLIO")

    def test_content_hash_tracks_source_and_ignores_drive_file_id(self):
        a = {"id": "one", "name": "sheet.pdf", "md5Checksum": "abc", "mimeType": "application/pdf"}
        b = {"id": "two", "name": "sheet.pdf", "md5Checksum": "abc", "mimeType": "application/pdf"}
        c = {**b, "md5Checksum": "def"}
        self.assertEqual(source_fingerprint(a), source_fingerprint(b))
        self.assertNotEqual(source_fingerprint(b), source_fingerprint(c))

    def test_deleted_source_removes_only_its_owned_product_and_preserves_legacy_manifest(self):
        current = {"products": {
            "gone": {"folder": "28_OLD"},
            "kept": {"folder": "29_KEEP"},
        }, "legacy_folders": ["OLD_UNTRACKED"]}
        self.assertEqual(removed_product_folders(current, {"kept"}), ["28_OLD"])
        changed = {"kept": {"folder": "30_RENAMED"}}
        self.assertEqual(removed_product_folders(current, {"kept", "gone"}, changed), ["29_KEEP"])
        self.assertEqual(removed_product_folders(["OLD_LEGACY"], set()), [])

    def test_shared_legacy_folder_is_not_removed_while_another_source_still_owns_it(self):
        shared = {"products": {
            "removed": {"folder": "28_SHARED"},
            "active": {"folder": "28_SHARED"},
        }}
        self.assertEqual(removed_product_folders(shared, {"active"}), [])
        updated = {"removed": {"folder": "29_NEW"}}
        self.assertEqual(removed_product_folders(shared, {"removed", "active"}, updated), [])

    def test_manifest_loader_migrates_old_list_without_scheduling_deletions(self):
        class ExistingPath:
            def exists(self):
                return True
            def read_text(self, encoding):
                return '["28_LEGACY"]'
        manifest = load_manifest(ExistingPath())
        self.assertEqual(manifest["legacy_folders"], ["28_LEGACY"])
        self.assertEqual(removed_product_folders(manifest, set()), [])

    def test_unchanged_sources_are_skipped_but_modified_or_new_sources_are_processed(self):
        a = {"id": "a", "name": "a.pdf", "md5Checksum": "x"}
        b = {"id": "b", "name": "b.pdf", "md5Checksum": "y"}
        manifest = {"products": {"a": product_manifest_entry(a, "28_A", {"ITA": "A"})}}
        self.assertEqual(unchanged_source_ids([a, b], manifest), {"a"})
        self.assertEqual(unchanged_source_ids([b], manifest), set())

    def test_moving_an_unchanged_source_from_intake_to_processed_keeps_its_product(self):
        from drive_sync_state import reconcile_sources

        source = {"id": "a", "name": "a.pdf", "md5Checksum": "x"}
        title = {"ITA": "A", "FR": "A FR", "ENG": "A EN", "NL": "A NL", "DE": "A DE"}
        entry = product_manifest_entry(source, "28_A", title)
        result = reconcile_sources([source], [], {"version": 1, "products": {"a": entry}})

        self.assertEqual(result["unchanged"], ["a"])
        self.assertEqual(result["removed_source_ids"], [])
        self.assertEqual(result["removed_folders"], [])
        self.assertEqual(result["next_products"]["a"], entry)

    def test_missing_processed_source_removes_only_its_owned_product(self):
        from drive_sync_state import reconcile_sources

        removed = {"id": "old", "name": "old.pdf", "md5Checksum": "x"}
        added = {"id": "new", "name": "new.pdf", "md5Checksum": "y"}
        entry = product_manifest_entry(removed, "28_OLD", {"ITA": "Old"})
        result = reconcile_sources([added], [], {"version": 2, "products": {"old": entry}})

        self.assertEqual(result["removed_source_ids"], ["old"])
        self.assertEqual(result["removed_folders"], ["28_OLD"])
        self.assertEqual(result["changed_pending"], [added])
        self.assertEqual(result["next_products"], {})

    def test_changed_active_fingerprint_schedules_update_without_deactivating_old_product(self):
        from drive_sync_state import reconcile_sources

        old = {"id": "a", "name": "a.pdf", "md5Checksum": "old"}
        updated = {"id": "a", "name": "a.pdf", "md5Checksum": "new"}
        entry = product_manifest_entry(old, "28_A", {"ITA": "A"})
        result = reconcile_sources([], [updated], {"version": 2, "products": {"a": entry}})

        self.assertEqual(result["changed_active"], [updated])
        self.assertEqual(result["removed_source_ids"], [])
        self.assertEqual(result["removed_folders"], [])
        self.assertEqual(result["next_products"]["a"], entry)

    def test_shared_product_folder_is_not_scheduled_for_removal_while_still_active(self):
        from drive_sync_state import reconcile_sources

        removed = {"id": "gone", "name": "gone.pdf", "md5Checksum": "x"}
        active = {"id": "kept", "name": "kept.pdf", "md5Checksum": "y"}
        entries = {
            "gone": product_manifest_entry(removed, "28_SHARED", {"ITA": "Shared"}),
            "kept": product_manifest_entry(active, "28_SHARED", {"ITA": "Shared"}),
        }
        result = reconcile_sources([], [active], {"version": 2, "products": entries})

        self.assertEqual(result["removed_source_ids"], ["gone"])
        self.assertEqual(result["removed_folders"], [])
        self.assertEqual(sorted(result["next_products"]), ["kept"])


if __name__ == "__main__":
    unittest.main()
