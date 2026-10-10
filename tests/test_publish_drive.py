import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_BUILD"))
from publish_drive import apply

FOLDER_MIME = "application/vnd.google-apps.folder"

class Request:
    def __init__(self, callback): self.callback = callback
    def execute(self): return self.callback()

class FakeFiles:
    def __init__(self, drive): self.drive = drive
    def list(self, q, **kwargs):
        parent = q.split("'")[1]
        name = q.split("name = '", 1)[1].split("'", 1)[0] if "name = '" in q else None
        results = [dict(item) for item in self.drive.items if parent in item.get("parents", []) and not item.get("trashed") and (name is None or item["name"] == name)]
        return Request(lambda: {"files": results})
    def create(self, body, media_body=None, fields=None, **kwargs):
        def run():
            item = {"id": f"id-{len(self.drive.items)}", **body}
            if media_body is not None:
                if hasattr(media_body, "filename"):
                    item["content"] = Path(media_body.filename).read_bytes()
                elif hasattr(media_body, "_fd"):
                    fd = media_body._fd
                    if hasattr(fd, "getvalue"):
                        item["content"] = fd.getvalue()
                    else:
                        fd.seek(0)
                        item["content"] = fd.read()
                else:
                    item["content"] = media_body.getbytes()
            self.drive.items.append(item)
            self.drive.events.append(("create", item["name"]))
            return item
        return Request(run)
    def get_media(self, fileId, **kwargs):
        item=next(x for x in self.drive.items if x["id"]==fileId)
        return item.get("content", b"{}")
    def get(self, fileId, **kwargs):
        item=next(x for x in self.drive.items if x["id"]==fileId)
        return Request(lambda: dict(item))
    def update(self, fileId, body=None, media_body=None, addParents=None, removeParents=None, **kwargs):
        def run():
            item = next(x for x in self.drive.items if x["id"] == fileId)
            if body: item.update(body)
            if media_body is not None:
                if hasattr(media_body, "filename"):
                    item["content"] = Path(media_body.filename).read_bytes()
                elif hasattr(media_body, "_fd"):
                    fd = media_body._fd
                    if hasattr(fd, "getvalue"):
                        item["content"] = fd.getvalue()
                    else:
                        fd.seek(0)
                        item["content"] = fd.read()
                else:
                    item["content"] = media_body.getbytes()
            if addParents:
                item.setdefault("parents", []).append(addParents)
            if removeParents:
                item["parents"] = [p for p in item.get("parents", []) if p != removeParents]
            self.drive.events.append(("update", item["name"]))
            return item
        return Request(run)

class FakeDrive:
    def __init__(self): self.items=[]; self.events=[]
    def files(self): return FakeFiles(self)
    def get_media(self, fileId, **kwargs):
        item=next(x for x in self.items if x["id"]==fileId)
        return item.get("content", b"{}")
    def get(self, fileId, **kwargs):
        item=next(x for x in self.items if x["id"]==fileId)
        return Request(lambda: dict(item))

def source_name(drive, source_id):
    return next(item["name"] for item in drive.items if item["id"] == source_id)


class PublishDriveTests(unittest.TestCase):
    def test_upserts_changed_product_trashes_only_owned_removal_moves_same_source_and_writes_manifest_last(self):
        drive = FakeDrive()
        old_manifest = {"version":2,"products":{"old-source":{"folder":"28_OLD"}},"legacy_folders":["01_LEGACY"]}
        drive.items.extend([
            {"id":"old-folder", "name":"28_OLD", "mimeType":FOLDER_MIME, "parents":["catalog"]},
            {"id":"manifest", "name":".technical-sheets-manifest.json", "mimeType":"application/json", "parents":["catalog"], "content":json.dumps(old_manifest).encode()},
            {"id":"legacy", "name":"01_LEGACY", "mimeType":FOLDER_MIME, "parents":["catalog"]},
            {"id":"unmanaged", "name":"29_UNMANAGED", "mimeType":FOLDER_MIME, "parents":["catalog"]},
            {"id":"source", "name":"new.pdf", "mimeType":"application/pdf", "parents":["intake"]},
        ])
        plan = {"status":"ready", "imported":{"28_NEW":{}}, "removed_folders":["28_OLD"],
                "move_source_ids":["source"], "source_folder_id":"intake", "next_manifest":{"version":2,"products":{"source":{"folder":"28_NEW"}},"legacy_folders":["01_LEGACY"]}}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); folder=root/"28_NEW"; folder.mkdir(); (folder/"28_NEW_ITA.pdf").write_bytes(b"pdf")
            result=apply(drive, plan, root, "catalog", "processed", None)
        self.assertEqual(result["trashed"], ["28_OLD"])
        self.assertEqual(next(x for x in drive.items if x["id"]=="manifest")["content"], json.dumps(plan["next_manifest"], ensure_ascii=False, indent=2).encode())
        self.assertEqual(next(x for x in drive.items if x["id"]=="legacy").get("trashed"), None)
        self.assertEqual(next(x for x in drive.items if x["id"]=="unmanaged").get("trashed"), None)
        source=next(x for x in drive.items if x["id"]=="source")
        self.assertEqual(source["parents"], ["processed"])
        self.assertEqual(source["id"], "source")
        self.assertEqual(drive.events[-1][0], "update")
        self.assertEqual(drive.events[-1][1], ".technical-sheets-manifest.json")
        manifest_event = drive.events[-1]
        self.assertEqual(manifest_event[0], "update")
        self.assertEqual(result["manifest_file_id"], "manifest")

    def test_retry_is_idempotent_after_source_move_and_manifest_update(self):
        drive=FakeDrive()
        source={"id":"source","name":"new.pdf","mimeType":"application/pdf","parents":["intake"]}
        drive.items.append(source)
        plan={"status":"ready","imported":{"28_NEW":{}},"removed_folders":[],"move_source_ids":["source"],"source_folder_id":"intake","next_manifest":{"version":2,"products":{"source":{"folder":"28_NEW"}},"legacy_folders":[]}}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); folder=root/"28_NEW"; folder.mkdir(); (folder/"28_NEW_ITA.pdf").write_bytes(b"pdf")
            first=apply(drive,plan,root,"catalog","processed",None)
            second=apply(drive,plan,root,"catalog","processed",first["manifest_file_id"])
        product_folders=[x for x in drive.items if x.get("name")=="28_NEW" and x.get("mimeType")==FOLDER_MIME]
        product_files=[x for x in drive.items if x.get("name")=="28_NEW_ITA.pdf"]
        self.assertEqual(len(product_folders),1)
        self.assertEqual(len(product_files),1)
        self.assertEqual(next(x for x in drive.items if x["id"]=="source")["parents"],["processed"])
        self.assertEqual(second["manifest_file_id"],first["manifest_file_id"])
        manifest_writes=[event for event in drive.events if event[1]==".technical-sheets-manifest.json"]
        self.assertEqual(len(manifest_writes),1)

    def test_source_files_are_renamed_only_during_finalize_and_before_manifest_write(self):
        drive = FakeDrive()
        source = {"id": "source", "name": "Supplier sheet.pdf", "mimeType": "application/pdf", "parents": ["processed"]}
        drive.items.append(source)
        entry = {"folder": "01_PRODUCT", "fingerprint": "x", "name": "Supplier sheet.pdf",
                 "original_name": "Supplier sheet.pdf", "managed_name": "01_PRODUCT__Supplier sheet.pdf", "title": {}}
        plan = {"status": "ready", "imported": {}, "removed_folders": [], "move_source_ids": [],
                "rename_sources": [{"id": "source", "from_name": "Supplier sheet.pdf", "to_name": entry["managed_name"]}],
                "next_manifest": {"version": 2, "products": {"source": entry}, "legacy_folders": []}}
        first = apply(drive, plan, Path("."), "catalog", "processed", None)
        first_events = list(drive.events)
        second = apply(drive, plan, Path("."), "catalog", "processed", first["manifest_file_id"])
        self.assertEqual(source["name"], entry["managed_name"])
        self.assertEqual(first["renamed_sources"], [{"id": "source", "name": entry["managed_name"]}])
        self.assertEqual(second["renamed_sources"], [])
        self.assertEqual(first_events[-2], ("update", entry["managed_name"]))
        self.assertEqual(first_events[-1], ("create", ".technical-sheets-manifest.json"))
        self.assertEqual(len(drive.events), len(first_events))

    def test_duplicate_source_is_moved_to_processed_and_renamed_as_error(self):
        drive = FakeDrive()
        source = {"id": "duplicate", "name": "Supplier sheet.pdf", "mimeType": "application/pdf",
                  "parents": ["intake"]}
        drive.items.append(source)
        error_name = "ERRORE: DUPLICATO - Supplier sheet [duplicate].pdf"
        plan = {"status": "ready", "imported": {}, "removed_folders": [],
                "move_source_ids": ["duplicate"], "source_folder_id": "intake",
                "rename_sources": [{"id": "duplicate", "from_name": source["name"], "to_name": error_name}],
                "next_manifest": {"version": 2, "products": {}, "legacy_folders": []}}
        result = apply(drive, plan, Path("."), "catalog", "processed", None)
        self.assertEqual(source["parents"], ["processed"])
        self.assertEqual(source["name"], error_name)
        self.assertEqual(result["renamed_sources"], [{"id": "duplicate", "name": error_name}])
        self.assertEqual(drive.events[:2], [("update", "Supplier sheet.pdf"), ("update", error_name)])

    def test_source_name_collision_blocks_all_finalize_mutations(self):
        drive = FakeDrive()
        drive.items.extend([
            {"id": "source", "name": "Original.pdf", "mimeType": "application/pdf", "parents": ["processed"]},
            {"id": "collision", "name": "01_PRODUCT__Original.pdf", "mimeType": "application/pdf", "parents": ["processed"]},
        ])
        plan = {"status": "ready", "imported": {}, "removed_folders": [], "move_source_ids": [],
                "rename_sources": [{"id": "source", "from_name": "Original.pdf", "to_name": "01_PRODUCT__Original.pdf"}],
                "next_manifest": {"version": 2, "products": {"source": {"folder": "01_PRODUCT"}}, "legacy_folders": []}}
        with self.assertRaisesRegex(RuntimeError, "source filename collision"):
            apply(drive, plan, Path("."), "catalog", "processed", None)
        self.assertEqual(source_name(drive, "source"), "Original.pdf")
        self.assertEqual(drive.events, [])

    def test_manifest_is_not_written_if_any_upsert_fails(self):
        class FailingDrive(FakeDrive):
            def files(self):
                files = super().files()
                original = files.create
                def create(body, media_body=None, **kwargs):
                    if body.get("name", "").endswith(".pdf"):
                        return Request(lambda: (_ for _ in ()).throw(RuntimeError("upload failed")))
                    return original(body, media_body=media_body, **kwargs)
                files.create = create
                return files
        drive=FailingDrive()
        plan={"status":"ready","imported":{"28_NEW":{}},"removed_folders":[],"move_source_ids":[],"source_folder_id":"intake","next_manifest":{"version":2,"products":{},"legacy_folders":[]}}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); folder=root/"28_NEW"; folder.mkdir(); (folder/"28_NEW_ITA.pdf").write_bytes(b"pdf")
            with self.assertRaisesRegex(RuntimeError,"upload failed"):
                apply(drive, plan, root, "catalog", "processed", None)
        self.assertFalse(any(x["name"]==".technical-sheets-manifest.json" for x in drive.items))

if __name__ == "__main__": unittest.main()
