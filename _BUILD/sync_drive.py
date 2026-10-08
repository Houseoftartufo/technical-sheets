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
from i18n import DATA_FILES

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "_BUILD"
FOLDER_ID = os.environ.get("DRIVE_SOURCE_FOLDER_ID") or "1Y1qgl2rih8Ikbjf6ch4CgG5Qtwg6k6hS"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
SUPPORTED = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"}


def drive_client():
    raw = os.environ.get("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON")
    if not raw:
        raise RuntimeError("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON is not configured")
    credentials = service_account.Credentials.from_service_account_info(json.loads(raw), scopes=SCOPES)
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def list_sources(drive):
    response = drive.files().list(
        q="'%s' in parents and trashed = false" % FOLDER_ID,
        pageSize=1000, fields="files(id,name,mimeType,modifiedTime,md5Checksum)",
        orderBy="name", supportsAllDrives=True, includeItemsFromAllDrives=True,
    ).execute()
    return [item for item in response.get("files", []) if item["mimeType"] in SUPPORTED]


def download(drive, item):
    request = drive.files().get_media(fileId=item["id"])
    from io import BytesIO
    buffer = BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buffer.getvalue()


def extract(client, item, content):
    uploaded = client.files.create(file=(item["name"], content), purpose="user_data")
    schema = {
        "type": "object", "additionalProperties": False,
        "properties": {
            "folder": {"type": "string"},
            "title": {"type": "object", "additionalProperties": {"type": "string"}},
            "general": {"type": "object", "additionalProperties": True},
            "ingredients": {"type": "object", "additionalProperties": True},
            "storage": {"type": "object", "additionalProperties": True},
            "nutrition": {"type": "object", "additionalProperties": {"type": "string"}},
            "characteristics": {"type": "object", "additionalProperties": True},
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
    client = OpenAI()
    errors, imported = [], {}
    existing = set()
    for filename in DATA_FILES:
        source = BUILD / filename
        if source.exists():
            existing.update(item["folder"] for item in json.loads(source.read_text(encoding="utf-8")))
    for item in list_sources(drive):
        try:
            product = extract(client, item, download(drive, item))
            validation = validate_product(product)
            if validation:
                errors.append({"file": item["name"], "errors": validation})
            else:
                folder = product["folder"]
                if folder in existing:
                    duplicate_folder = "DUPLICATE_%s" % folder
                    product["duplicate_of"] = folder
                    product["folder"] = duplicate_folder
                    folder = duplicate_folder
                imported[folder] = product
        except Exception as exc:
            errors.append({"file": item["name"], "errors": [str(exc)]})
    if errors:
        report = {"status": "blocked", "errors": errors, "imported": list(imported)}
        (BUILD / "drive_sync_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        raise SystemExit("Drive import blocked; see _BUILD/drive_sync_report.json")
    previous_path = BUILD / "drive_manifest.json"
    previous = set(json.loads(previous_path.read_text(encoding="utf-8"))) if previous_path.exists() else set()
    current = set(imported)
    (BUILD / "removed_products.json").write_text(json.dumps(sorted(previous - current), ensure_ascii=False, indent=2), encoding="utf-8")
    (BUILD / "drive_manifest.json").write_text(json.dumps(sorted(current), ensure_ascii=False, indent=2), encoding="utf-8")
    (BUILD / "product_overrides.json").write_text(json.dumps(imported, ensure_ascii=False, indent=2), encoding="utf-8")
    (BUILD / "drive_sync_report.json").write_text(json.dumps({"status": "ready", "imported": list(imported), "errors": []}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Drive sync ready:", len(imported), "products")


if __name__ == "__main__":
    main()
