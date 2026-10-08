"""Publish generated product folders and finalize the authoritative Drive manifest."""
import json
import mimetypes
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED_ROOT = Path(os.environ.get("DRIVE_GENERATED_DIR", ROOT))
CATALOG_ID = os.environ.get("DRIVE_CATALOG_FOLDER_ID") or "1vEyctBT3z9F5-hFM-DeTWEsjaY2I8drb"
SCOPES = ["https://www.googleapis.com/auth/drive"]
MANIFEST_NAME = ".technical-sheets-manifest.json"
FOLDER_MIME = "application/vnd.google-apps.folder"
EMPTY_FOLDER_ALIASES = {"28_CARPACCIO_DI_TARTUFO_ESTIVO_IN_OLIO": ("CARPACCIO_DI_TARTUFO_ESTIVO",)}


def drive_client():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    raw = os.environ.get("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON")
    if not raw:
        raise RuntimeError("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON is not configured")
    credentials = service_account.Credentials.from_service_account_info(json.loads(raw), scopes=SCOPES)
    impersonated_user = os.environ.get("GOOGLE_DRIVE_IMPERSONATED_USER")
    if impersonated_user:
        credentials = credentials.with_subject(impersonated_user)
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def escaped(value):
    return value.replace("'", "\\'")


def child_items(drive, parent_id, name, mime_type=None):
    clauses = [f"'{parent_id}' in parents", "trashed = false", f"name = '{escaped(name)}'"]
    if mime_type:
        clauses.append(f"mimeType = '{mime_type}'")
    return drive.files().list(
        q=" and ".join(clauses), pageSize=100, fields="files(id,name,mimeType,parents,md5Checksum,size)",
        supportsAllDrives=True, includeItemsFromAllDrives=True,
    ).execute().get("files", [])


def ensure_product_folder(drive, folder, catalog_id=None):
    catalog_id = catalog_id or CATALOG_ID
    folders = child_items(drive, catalog_id, folder, FOLDER_MIME)
    if len(folders) > 1:
        raise RuntimeError(f"Multiple Drive folders named {folder}; refusing ambiguous update")
    if folders:
        return folders[0]["id"]
    for alias in EMPTY_FOLDER_ALIASES.get(folder, ()):
        candidates = child_items(drive, catalog_id, alias, FOLDER_MIME)
        for candidate in candidates:
            children = drive.files().list(
                q=f"'{candidate['id']}' in parents and trashed = false", pageSize=1,
                fields="files(id)", supportsAllDrives=True, includeItemsFromAllDrives=True,
            ).execute().get("files", [])
            if not children:
                drive.files().update(fileId=candidate["id"], body={"name": folder},
                                     fields="id", supportsAllDrives=True).execute()
                return candidate["id"]
    return drive.files().create(
        body={"name": folder, "mimeType": FOLDER_MIME, "parents": [catalog_id]},
        fields="id", supportsAllDrives=True,
    ).execute()["id"]


def upsert_file(drive, parent_id, path):
    from googleapiclient.http import MediaFileUpload

    matches = child_items(drive, parent_id, path.name)
    if len(matches) > 1:
        raise RuntimeError(f"Multiple Drive files named {path.name} in output folder")
    media = MediaFileUpload(str(path), mimetype=mimetypes.guess_type(path.name)[0] or "application/octet-stream")
    if matches:
        drive.files().update(fileId=matches[0]["id"], media_body=media, supportsAllDrives=True).execute()
        return matches[0]["id"]
    return drive.files().create(body={"name": path.name, "parents": [parent_id]}, media_body=media,
                                fields="id", supportsAllDrives=True).execute()["id"]


def _trash_owned_folders(drive, catalog_id, folders):
    trashed = []
    for folder in sorted(set(folders)):
        matches = child_items(drive, catalog_id, folder, FOLDER_MIME)
        if len(matches) > 1:
            raise RuntimeError(f"Multiple Drive folders named {folder}; refusing ambiguous removal")
        if matches:
            drive.files().update(fileId=matches[0]["id"], body={"trashed": True},
                                 supportsAllDrives=True).execute()
            trashed.append(folder)
    return trashed


def _manifest_items(drive, catalog_id, manifest_file_id):
    if manifest_file_id:
        return [{"id": manifest_file_id, "name": MANIFEST_NAME}]
    return child_items(drive, catalog_id, MANIFEST_NAME)


def download_drive_file(drive, item):
    from googleapiclient.http import MediaIoBaseDownload
    from io import BytesIO

    request = drive.files().get_media(fileId=item["id"], supportsAllDrives=True)
    if isinstance(request, (bytes, bytearray)):
        return bytes(request)
    buffer = BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buffer.getvalue()


def _upsert_manifest(drive, catalog_id, payload, existing_id):
    from googleapiclient.http import MediaInMemoryUpload

    data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    media = MediaInMemoryUpload(data, mimetype="application/json", resumable=False)
    if existing_id:
        drive.files().update(fileId=existing_id, media_body=media, supportsAllDrives=True).execute()
        return existing_id
    return drive.files().create(
        body={"name": MANIFEST_NAME, "mimeType": "application/json", "parents": [catalog_id]},
        media_body=media, fields="id", supportsAllDrives=True,
    ).execute()["id"]


def _validate_plan(plan):
    if plan.get("status") != "ready":
        raise RuntimeError("Refusing to publish a blocked Drive sync plan")
    manifest = plan.get("next_manifest")
    if not isinstance(manifest, dict) or manifest.get("version") != 2 or not isinstance(manifest.get("products"), dict):
        raise ValueError("Drive sync plan has no valid v2 manifest")
    if plan.get("move_source_ids") and not plan.get("source_folder_id"):
        raise ValueError("Drive sync plan is missing its intake folder ID")


def apply(drive, plan, generated_root, catalog_id, processed_id, manifest_file_id=None):
    """Idempotently publish changed outputs, remove owned folders, move sources, then commit manifest."""
    _validate_plan(plan)
    generated_root = Path(generated_root)
    next_manifest = plan["next_manifest"]
    products = next_manifest["products"]
    active_folders = {entry.get("folder") for entry in products.values() if entry.get("folder")}
    active_folders.update(plan.get("imported", {}).keys())

    existing_manifest_items = _manifest_items(drive, catalog_id, manifest_file_id)
    if len(existing_manifest_items) > 1:
        raise RuntimeError("Multiple Drive sync manifests found; refusing to choose one")
    existing_manifest_id = existing_manifest_items[0]["id"] if existing_manifest_items else None
    previous_manifest = json.loads(download_drive_file(drive, existing_manifest_items[0])) if existing_manifest_items else {"version": 2, "products": {}, "legacy_folders": []}
    previous_products = previous_manifest.get("products", {})
    owned_folders = {entry.get("folder") for entry in previous_products.values() if entry.get("folder")}
    removed_candidates = set(plan.get("removed_folders", []))
    next_owned = {entry.get("folder") for entry in products.values() if entry.get("folder")}
    next_owned.update(plan.get("imported", {}).keys())
    safe_removed = (removed_candidates & owned_folders) - next_owned
    if safe_removed != removed_candidates - next_owned:
        unsafe = sorted((removed_candidates - next_owned) - owned_folders)
        if unsafe:
            raise RuntimeError("Removal requested for folders not owned by the sync manifest: " + ", ".join(unsafe))

    published = []
    for folder in sorted(plan.get("imported", {})):
        if folder not in active_folders:
            raise RuntimeError(f"Changed product is absent from active manifest: {folder}")
        product_dir = generated_root / folder
        if not product_dir.is_dir():
            raise RuntimeError(f"Generated product folder is missing: {folder}")
        files = sorted(product_dir.glob(f"{folder}_*.html")) + sorted(product_dir.glob(f"{folder}_*.pdf"))
        if not files:
            raise RuntimeError(f"No generated HTML/PDF files found for {folder}")
        destination_id = ensure_product_folder(drive, folder, catalog_id)
        output_ids = [upsert_file(drive, destination_id, path) for path in files]
        published.append({"folder": folder, "files": [path.name for path in files], "drive_ids": output_ids})

    trashed = _trash_owned_folders(drive, catalog_id, safe_removed)

    moved = []
    source_folder_id = plan.get("source_folder_id")
    for source_id in sorted(set(plan.get("move_source_ids", []))):
        found = drive.files().get(fileId=source_id, fields="id,parents", supportsAllDrives=True).execute()
        parents = found.get("parents", [])
        if processed_id in parents:
            continue
        if source_folder_id not in parents:
            raise RuntimeError(f"Intake source {source_id} is no longer in the expected folder")
        drive.files().update(fileId=source_id, addParents=processed_id, removeParents=source_folder_id,
                             fields="id,parents", supportsAllDrives=True).execute()
        moved.append(source_id)

    if existing_manifest_id and previous_manifest == next_manifest:
        saved_manifest_id = existing_manifest_id
    else:
        saved_manifest_id = _upsert_manifest(drive, catalog_id, next_manifest, existing_manifest_id)
    return {"published_to_drive": published, "trashed": trashed, "moved_source_ids": moved,
            "manifest_file_id": saved_manifest_id, "active_product_folders": sorted(active_folders)}


def main():
    """Legacy CLI remains for manual debugging; orchestration calls apply after deploy."""
    raise SystemExit("Use the sync-drive workflow, which finalizes Drive after a verified Vercel deploy.")


if __name__ == "__main__":
    main()
