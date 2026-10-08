import hashlib
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_BUILD"))

from build_site_bundle import assemble_site_bundle
from build_index import load_static_titles
from i18n import LANGS


def expected_names(folder):
    return [f"{folder}_{language}.{extension}"
            for extension in ("html", "pdf") for language in LANGS]


def make_drive_product(drive, catalog_id, folder, marker="old"):
    folder_id = f"drive-{folder}"
    drive.items.append({"id": folder_id, "name": folder, "mimeType": "application/vnd.google-apps.folder", "parents": [catalog_id]})
    contents = {}
    for filename in expected_names(folder):
        item_id = f"{folder_id}-{filename}"
        drive.items.append({
            "id": item_id, "name": filename,
            "mimeType": "application/pdf" if filename.endswith(".pdf") else "text/html",
            "parents": [folder_id],
        })
        contents[item_id] = (b"%PDF-1.4 " + marker.encode()) if filename.endswith(".pdf") else f"<html>{marker}</html>".encode()
    return contents


class Request:
    def __init__(self, value):
        self.value = value

    def execute(self):
        return self.value


class FakeFiles:
    def __init__(self, drive):
        self.drive = drive

    def list(self, q, **kwargs):
        parent = q.split("'")[1]
        name = q.split("name = '", 1)[1].split("'", 1)[0] if "name = '" in q else None
        mime = q.split("mimeType = '", 1)[1].split("'", 1)[0] if "mimeType = '" in q else None
        found = [item for item in self.drive.items
                 if parent in item.get("parents", [])
                 and not item.get("trashed")
                 and (name is None or item["name"] == name)
                 and (mime is None or item["mimeType"] == mime)]
        return Request({"files": found})


class FakeDrive:
    def __init__(self):
        self.items = []

    def files(self):
        return FakeFiles(self)


class BuildSiteBundleTests(unittest.TestCase):
    def test_all_27_static_product_outputs_are_copied_byte_for_byte(self):
        repo = Path(__file__).resolve().parents[1]
        expected = {}
        for folder in load_static_titles():
            for path in (repo / folder).iterdir():
                if path.is_file():
                    expected[f"{folder}/{path.name}"] = hashlib.sha256(path.read_bytes()).hexdigest()

        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "site"
            result = assemble_site_bundle(repo, Path(temp) / "generated", {}, FakeDrive(), "catalog", output)
            actual = {
                f"{folder.name}/{path.name}": hashlib.sha256(path.read_bytes()).hexdigest()
                for folder in result.iterdir() if folder.is_dir() and folder.name in load_static_titles()
                for path in folder.iterdir() if path.is_file()
            }

        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 270)

    def test_bundle_downloads_unchanged_active_product_and_index_links_resolve(self):
        repo = Path(__file__).resolve().parents[1]
        titles = {language: f"Active {language}" for language in LANGS}
        drive = FakeDrive()
        payloads = make_drive_product(drive, "catalog", "28_ACTIVE", "kept")
        with tempfile.TemporaryDirectory() as temp, \
             patch("build_site_bundle.download_drive_file", side_effect=lambda _drive, item: payloads[item["id"]]):
            output = Path(temp) / "site"
            result = assemble_site_bundle(repo, Path(temp) / "generated", {"28_ACTIVE": titles}, drive, "catalog", output)
            index = (result / "index.html").read_text(encoding="utf-8")

            links = re.findall(r'href="(28_ACTIVE/[^\"]+\.pdf)"', index)
            self.assertEqual(len(links), len(LANGS))
            self.assertTrue(all((result / link).is_file() for link in links))
            self.assertEqual((result / "28_ACTIVE" / "28_ACTIVE_DE.pdf").read_bytes(), payloads["drive-28_ACTIVE-28_ACTIVE_DE.pdf"])
            self.assertIn("Active DE", index)

    def test_changed_product_overlays_drive_copy_and_unlisted_generated_files_are_excluded(self):
        repo = Path(__file__).resolve().parents[1]
        drive = FakeDrive()
        payloads = make_drive_product(drive, "catalog", "29_CHANGED", "old")
        titles = {language: f"Changed {language}" for language in LANGS}
        with tempfile.TemporaryDirectory() as temp, \
             patch("build_site_bundle.download_drive_file", side_effect=lambda _drive, item: payloads[item["id"]]):
            generated = Path(temp) / "generated"
            product = generated / "29_CHANGED"
            product.mkdir(parents=True)
            for filename in expected_names("29_CHANGED"):
                (product / filename).write_bytes(b"new-version")
            stray = generated / "99_NOT_ACTIVE"
            stray.mkdir()
            (stray / "unlisted.pdf").write_bytes(b"stray")
            output = Path(temp) / "site"
            result = assemble_site_bundle(repo, generated, {"29_CHANGED": titles}, drive, "catalog", output)
            self.assertEqual((result / "29_CHANGED" / "29_CHANGED_DE.pdf").read_bytes(), b"new-version")
            self.assertFalse((result / "99_NOT_ACTIVE").exists())


if __name__ == "__main__":
    unittest.main()
