"""Publish generated product folders to the official Google Drive catalog."""
import json
import mimetypes
import os
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT = Path(__file__).resolve().parents[1]
CATALOG_ID = os.environ.get("DRIVE_CATALOG_FOLDER_ID") or "1vEyctBT3z9F5-hFM-DeTWEsjaY2I8drb"
SCOPES = ["https://www.googleapis.com/auth/drive"]


def drive_client():
    raw = os.environ.get("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON")
    if not raw:
        raise RuntimeError("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON is not configured")
    credentials = service_account.Credentials.from_service_account_info(json.loads(raw), scopes=SCOPES)
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def escaped(value):
    return value.replace("'", "\\'")


def child_items(drive, parent_id, name, mime_type=None):
    clauses = [f"'{parent_id}' in parents", "trashed = false", f"name = '{escaped(name)}'"]
    if mime_type:
        clauses.append(f"mimeType = '{mime_type}'")
    return drive.files().list(
        q=" and ".join(clauses), pageSize=100, fields="files(id,name,mimeType)",
        supportsAllDrives=True, includeItemsFromAllDrives=True,
    ).execute().get("files", [])


def ensure_product_folder(drive, folder):
    folders = child_items(drive, CATALOG_ID, folder, "application/vnd.google-apps.folder")
    if folders:
        return folders[0]["id"]
    return drive.files().create(
        body={"name": folder, "mimeType": "application/vnd.google-apps.folder", "parents": [CATALOG_ID]},
        fields="id", supportsAllDrives=True,
    ).execute()["id"]


def upsert_file(drive, parent_id, path):
    query = f"'{parent_id}' in parents and trashed = false and name = '{escaped(path.name)}'"
    matches = drive.files().list(q=query, pageSize=10, fields="files(id)", supportsAllDrives=True,
                                 includeItemsFromAllDrives=True).execute().get("files", [])
    media = MediaFileUpload(str(path), mimetype=mimetypes.guess_type(path.name)[0] or "application/octet-stream")
    if matches:
        drive.files().update(fileId=matches[0]["id"], media_body=media, supportsAllDrives=True).execute()
    else:
        drive.files().create(body={"name": path.name, "parents": [parent_id]}, media_body=media,
                             fields="id", supportsAllDrives=True).execute()


def trash_product_folder(drive, folder):
    for item in child_items(drive, CATALOG_ID, folder, "application/vnd.google-apps.folder"):
        drive.files().update(fileId=item["id"], body={"trashed": True}, supportsAllDrives=True).execute()


def main():
    drive = drive_client()
    overrides_path = ROOT / "_BUILD" / "product_overrides.json"
    removed_path = ROOT / "_BUILD" / "removed_products.json"
    products = json.loads(overrides_path.read_text(encoding="utf-8")) if overrides_path.exists() else {}
    removed = json.loads(removed_path.read_text(encoding="utf-8")) if removed_path.exists() else []
    published = []
    for folder in sorted(products):
        product_dir = ROOT / folder
        if not product_dir.is_dir():
            raise RuntimeError(f"Generated product folder is missing: {folder}")
        drive_folder = ensure_product_folder(drive, folder)
        files = sorted(product_dir.glob(f"{folder}_*.html")) + sorted(product_dir.glob(f"{folder}_*.pdf"))
        if not files:
            raise RuntimeError(f"No generated HTML/PDF files found for {folder}")
        for path in files:
            upsert_file(drive, drive_folder, path)
        published.append({"folder": folder, "files": [path.name for path in files]})
    for folder in removed:
        trash_product_folder(drive, folder)
    report_path = ROOT / "_BUILD" / "drive_sync_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
    report.update({"published_to_drive": published, "trashed_from_drive": sorted(removed)})
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Drive catalog published: {len(published)} product folders; trashed: {len(removed)}")


if __name__ == "__main__":
    main()
