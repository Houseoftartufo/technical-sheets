"""Assemble a complete static-site bundle from legacy files and active Drive products."""
from io import BytesIO
import json
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
