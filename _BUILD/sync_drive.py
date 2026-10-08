"""Import supplier PDFs/DOCX files from Drive into the existing catalog engine.

The Drive folder is an input queue. Generated product records are stored in
product_overrides.json and are rendered by the same engine.py/build_index.py.
"""
import json
import os
import re
import sys
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from openai import OpenAI

from drive_schema import LANGS, validate_product
from drive_sync_state import (
    canonicalize_product, load_manifest, product_manifest_entry,
    removed_product_folders, resolve_output_folder, unchanged_source_ids,
)
from i18n import DATA_FILES

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "_BUILD"
FOLDER_ID = os.environ.get("DRIVE_SOURCE_FOLDER_ID") or "1Y1qgl2rih8Ikbjf6ch4CgG5Qtwg6k6hS"
CATALOG_ID = os.environ.get("DRIVE_CATALOG_FOLDER_ID") or "1vEyctBT3z9F5-hFM-DeTWEsjaY2I8drb"
SCOPES = ["https://www.googleapis.com/auth/drive"]
SUPPORTED = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"}


def drive_client():
    raw = os.environ.get("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON")
    if not raw:
        raise RuntimeError("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON is not configured")
    credentials = service_account.Credentials.from_service_account_info(json.loads(raw), scopes=SCOPES)
    impersonated_user = os.environ.get("GOOGLE_DRIVE_IMPERSONATED_USER")
    if impersonated_user:
        credentials = credentials.with_subject(impersonated_user)
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def list_sources(drive):
    response = drive.files().list(
        q="'%s' in parents and trashed = false" % FOLDER_ID,
        pageSize=1000, fields="files(id,name,mimeType,modifiedTime,md5Checksum)",
        orderBy="name", supportsAllDrives=True, includeItemsFromAllDrives=True,
    ).execute()
    return [item for item in response.get("files", []) if item["mimeType"] in SUPPORTED]


def download(drive, item):
    request = drive.files().get_media(fileId=item["id"], supportsAllDrives=True)
    from io import BytesIO
    buffer = BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buffer.getvalue()


def extract(client, item, content):
    uploaded = client.files.create(file=(item["name"], content), purpose="user_data")
    def localized_schema():
        return {
            "type": "object",
            "properties": {language: {"type": "string"} for language in LANGS},
            "required": list(LANGS),
            "additionalProperties": False,
        }

    def object_schema(properties):
        return {
            "type": "object",
            "properties": properties,
            "required": list(properties),
            "additionalProperties": False,
        }

    schema = {
        "type": "object", "additionalProperties": False,
        "properties": {
            "folder": {"type": "string"},
            "title": localized_schema(),
            "general": object_schema({
                "ean": {"type": "string"},
                "typology": localized_schema(),
                "shelf": localized_schema(),
                "packaging": localized_schema(),
                "labelling": localized_schema(),
                "gmo": localized_schema(),
            }),
            "ingredients": object_schema({
                "ingredients": localized_schema(),
                "allergens": localized_schema(),
            }),
            "storage": object_schema({
                "instructions": localized_schema(),
                "method": localized_schema(),
            }),
            "nutrition": object_schema({
                name: {"type": "string"}
                for name in ("energy", "fat", "sat", "carb", "sugar", "protein", "salt", "fibre")
            }),
            "characteristics": object_schema({
                "chemical": localized_schema(),
                "micro": localized_schema(),
            }),
        },
        "required": ["folder", "title", "general", "ingredients", "storage", "nutrition", "characteristics"],
    }
    instruction = (
        "Extract this supplier technical sheet into the supplied JSON schema. "
        "Translate every localized field into ITA, FR, ENG, NL, DE. Preserve exact numbers, units, percentages, "
        "ingredient order, botanical names, allergens and legal text. Leave unknown values as empty strings. "
        "Use the product folder identifier in uppercase with underscores."
    )
    response = client.responses.create(
        model=os.environ.get("OPENAI_IMPORT_MODEL", "gpt-4.1"),
        input=[{"role": "user", "content": [
            {"type": "input_file", "file_id": uploaded.id, "detail": "high"},
            {"type": "input_text", "text": instruction},
        ]}],
        text={"format": {"type": "json_schema", "name": "technical_sheet", "strict": True, "schema": schema}},
    )
    return json.loads(response.output_text)


def main():
    drive = drive_client()
    catalog = drive.files().get(
        fileId=CATALOG_ID, fields="id,name,driveId", supportsAllDrives=True,
    ).execute()
    if not catalog.get("driveId") and not os.environ.get("GOOGLE_DRIVE_IMPERSONATED_USER"):
        raise SystemExit(
            "The catalog folder is in My Drive, but service accounts have no Drive storage quota. "
            "Use a Shared Drive or configure Google Workspace domain-wide delegation and set "
            "GOOGLE_DRIVE_IMPERSONATED_USER before importing supplier documents."
        )
    client = OpenAI()
    errors, imported, processed_entries = [], {}, {}
    existing = set()
    for filename in DATA_FILES:
        source = BUILD / filename
        if source.exists():
            existing.update(item["folder"] for item in json.loads(source.read_text(encoding="utf-8")))

    sources = list_sources(drive)
    previous_path = BUILD / "drive_manifest.json"
    previous = load_manifest(previous_path)
    unchanged = unchanged_source_ids(sources, previous)
    reserved_folders = {
        entry.get("folder") for source_id, entry in previous.get("products", {}).items()
        if source_id in unchanged and entry.get("folder")
    }
    for item in sources:
        if item["id"] in unchanged:
            continue
        try:
            product = extract(client, item, download(drive, item))
            product = canonicalize_product(product, item["name"])
            validation = validate_product(product)
            if validation:
                errors.append({"file": item["name"], "errors": validation})
            else:
                folder, collision = resolve_output_folder(product, existing, imported, reserved_folders)
                if collision:
                    errors.append({"file": item["name"], "errors": [collision]})
                    continue
                imported[folder] = product
                processed_entries[item["id"]] = product_manifest_entry(item, folder)
        except Exception as exc:
            errors.append({"file": item["name"], "errors": [str(exc)]})
    if errors:
        report = {"status": "blocked", "errors": errors, "imported": list(imported),
                  "unchanged": len(unchanged)}
        report_text = json.dumps(report, ensure_ascii=False, indent=2)
        (BUILD / "drive_sync_report.json").write_text(report_text, encoding="utf-8")
        print(report_text, file=sys.stderr)
        raise SystemExit("Drive import blocked; see _BUILD/drive_sync_report.json")

    current_ids = {item["id"] for item in sources}
    removed = removed_product_folders(previous, current_ids, processed_entries)
    next_products = {
        source_id: entry for source_id, entry in previous.get("products", {}).items()
        if source_id in current_ids
    }
    next_products.update(processed_entries)
    manifest = {"version": 1, "products": next_products,
                "legacy_folders": previous.get("legacy_folders", [])}
    (BUILD / "removed_products.json").write_text(json.dumps(removed, ensure_ascii=False, indent=2), encoding="utf-8")
    previous_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (BUILD / "product_overrides.json").write_text(json.dumps(imported, ensure_ascii=False, indent=2), encoding="utf-8")
    (BUILD / "drive_sync_report.json").write_text(json.dumps({"status": "ready", "imported": list(imported), "unchanged": len(unchanged), "removed": removed, "errors": []}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Drive sync ready:", len(imported), "changed products;", len(unchanged), "unchanged")


if __name__ == "__main__":
    main()
