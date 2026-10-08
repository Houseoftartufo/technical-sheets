"""Assemble a complete static-site bundle from legacy files and active Drive products."""
from io import BytesIO
import json
import os
from pathlib import Path
import shutil
import tempfile

from build_index import build_index, load_static_titles
from i18n import LANGS


EXPECTED_EXTENSIONS = ("html", "pdf")
FOLDER_MIME = "application/vnd.google-apps.folder"


def expected_product_files(folder):
    return [f"{folder}_{language}.{extension}"
            for extension in EXPECTED_EXTENSIONS for language in LANGS]


def download_drive_file(drive, item):
    from googleapiclient.http import MediaIoBaseDownload

    request = drive.files().get_media(fileId=item["id"], supportsAllDrives=True)
    buffer = BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buffer.getvalue()


def _drive_folder(drive, catalog_id, folder):
    escaped = folder.replace("'", "\\'")
    query = (f"'{catalog_id}' in parents and trashed = false and name = '{escaped}' "
             f"and mimeType = '{FOLDER_MIME}'")
    result = drive.files().list(
        q=query, pageSize=100, fields="files(id,name,mimeType)",
        supportsAllDrives=True, includeItemsFromAllDrives=True,
    ).execute().get("files", [])
    if len(result) != 1:
        raise RuntimeError(f"Expected one Drive product folder for {folder}, found {len(result)}")
    return result[0]


def _copy_drive_product(drive, catalog_id, folder, destination):
    drive_folder = _drive_folder(drive, catalog_id, folder)
    result = drive.files().list(
        q=f"'{drive_folder['id']}' in parents and trashed = false", pageSize=1000,
        fields="files(id,name,mimeType)", supportsAllDrives=True, includeItemsFromAllDrives=True,
    ).execute().get("files", [])
    by_name = {}
    for item in result:
        by_name.setdefault(item["name"], []).append(item)
    destination.mkdir(parents=True, exist_ok=True)
    for filename in expected_product_files(folder):
        matches = by_name.get(filename, [])
        if len(matches) != 1:
            raise RuntimeError(f"Expected one Drive output {folder}/{filename}, found {len(matches)}")
        (destination / filename).write_bytes(download_drive_file(drive, matches[0]))


def _validate_product_files(folder, directory):
    missing = [filename for filename in expected_product_files(folder)
               if not (directory / filename).is_file()]
    if missing:
        raise RuntimeError(f"Product {folder} is missing generated files: {', '.join(missing)}")


def migrate_legacy_product_titles(drive, catalog_id, manifest, active_products):
    """Recover localized titles from existing HTML for v1 manifest entries without titles."""
    from html.parser import HTMLParser

    class TitleParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.depth = 0
            self.value = []
        def handle_starttag(self, tag, attrs):
            if tag == "div" and "product-title" in dict(attrs).get("class", "").split():
                self.depth += 1
        def handle_endtag(self, tag):
            if tag == "div" and self.depth:
                self.depth -= 1
        def handle_data(self, data):
            if self.depth:
                self.value.append(data)

    for entry in manifest.get("products", {}).values():
        folder = entry.get("folder")
        if not folder or folder not in active_products:
            continue
        if all(entry.get("title", {}).get(language) for language in LANGS):
            continue
        folder_obj = _drive_folder(drive, catalog_id, folder)
        product_files = drive.files().list(
            q=f"'{folder_obj['id']}' in parents and trashed = false", pageSize=1000,
            fields="files(id,name,mimeType)", supportsAllDrives=True, includeItemsFromAllDrives=True,
        ).execute().get("files", [])
        by_name = {}
        for item in product_files:
            by_name.setdefault(item["name"], []).append(item)
        localized = {}
        for language in LANGS:
            filename = f"{folder}_{language}.html"
            matches = by_name.get(filename, [])
            if len(matches) != 1:
                raise RuntimeError(f"Cannot migrate title for {folder} {language}: expected one existing HTML")
            html = download_drive_file(drive, matches[0]).decode("utf-8")
            parser = TitleParser()
            parser.feed(html)
            localized[language] = "".join(parser.value).strip()
        if not all(localized.values()):
            raise RuntimeError(f"Cannot migrate all localized titles for {folder}")
        entry["title"] = localized
        active_products[folder] = localized
    manifest["version"] = 2
    manifest.setdefault("legacy_folders", [])
    return active_products


def assemble_site_bundle(repo_root, generated_root, active_products, drive, catalog_id, output_root):
    """Copy public assets, unchanged active Drive outputs and generated updates into an empty bundle."""
    repo_root = Path(repo_root).resolve()
    generated_root = Path(generated_root).resolve()
    output_root = Path(output_root).resolve()
    if output_root == repo_root or output_root.is_relative_to(repo_root):
        raise ValueError("site bundle output must be outside the repository root")
    if output_root.exists() and any(output_root.iterdir()):
        raise ValueError("site bundle output directory must be empty")
    output_root.mkdir(parents=True, exist_ok=True)

    static_titles = load_static_titles()
    for folder in sorted(static_titles):
        source = repo_root / folder
        if not source.is_dir():
            raise RuntimeError(f"Static product folder is missing: {folder}")
        destination = output_root / folder
        shutil.copytree(source, destination)
        _validate_product_files(folder, destination)

    for filename in ("house-of-tartufo-logo.png", "vercel.json"):
        source = repo_root / filename
        if source.is_file():
            shutil.copy2(source, output_root / filename)

    for folder in sorted(active_products):
        if not isinstance(folder, str) or not folder or Path(folder).name != folder or folder in (".", ".."):
            raise ValueError(f"Unsafe managed product folder: {folder!r}")
        generated = generated_root / folder
        destination = output_root / folder
        if generated.is_dir():
            shutil.copytree(generated, destination)
            _validate_product_files(folder, destination)
        else:
            _copy_drive_product(drive, catalog_id, folder, destination)
            _validate_product_files(folder, destination)

    with tempfile.TemporaryDirectory(prefix="drive-site-index-") as temp:
        metadata = Path(temp) / "active-products.json"
        metadata.write_text(json.dumps(active_products, ensure_ascii=False, indent=2), encoding="utf-8")
        build_index([
            "--site-root", str(output_root),
            "--output", str(output_root / "index.html"),
            "--dynamic-products", str(metadata),
        ])
    return output_root


def main():
    from sync_drive import drive_client, load_manifest_bytes
    from publish_drive import download_drive_file

    repo_root = Path(__file__).resolve().parents[1]
    run_dir = Path(os.environ["DRIVE_RUN_DIR"])
    output_root = Path(os.environ["SITE_BUNDLE_DIR"])
    catalog_id = os.environ["DRIVE_CATALOG_FOLDER_ID"]
    drive = drive_client()
    manifest_matches = drive.files().list(
        q=f"'{catalog_id}' in parents and trashed = false and name = '.technical-sheets-manifest.json'",
        pageSize=10, fields="files(id,name)", supportsAllDrives=True, includeItemsFromAllDrives=True,
    ).execute().get("files", [])
    if len(manifest_matches) > 1:
        raise RuntimeError("Multiple Drive sync manifests found")
    plan = json.loads((run_dir / "drive_sync_plan.json").read_text(encoding="utf-8"))
    if plan.get("status") != "ready":
        raise RuntimeError("Cannot assemble bundle for blocked Drive plan")
    manifest = load_manifest_bytes(download_drive_file(drive, manifest_matches[0])) if manifest_matches else plan["next_manifest"]
    active = plan["active_products"]
    migrate_legacy_product_titles(drive, catalog_id, manifest, active)
    plan["next_manifest"]=manifest
    plan["active_products"]=active
    (run_dir / "drive_sync_plan.json").write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding="utf-8")
    assemble_site_bundle(repo_root, Path(os.environ["DRIVE_GENERATED_DIR"]), active, drive, catalog_id, output_root)
    print(f"Validated Vercel bundle with {len(active)} managed products")


if __name__ == "__main__":
    main()
