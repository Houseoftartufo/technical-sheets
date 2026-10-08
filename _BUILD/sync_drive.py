"""Import supplier PDFs/DOCX files from Drive into the existing catalog engine.

The Drive folder is an input queue. Generated product records are stored in
product_overrides.json and are rendered by the same engine.py/build_index.py.
"""
import json
import os
import re
import sys
from pathlib import Path

from drive_schema import LANGS, validate_product
from drive_sync_state import (
    canonicalize_product, load_manifest, product_manifest_entry,
    reconcile_sources, removed_product_folders, resolve_output_folder, source_fingerprint,
)
from i18n import DATA_FILES

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "_BUILD"
FOLDER_ID = os.environ.get("DRIVE_SOURCE_FOLDER_ID") or "1Y1qgl2rih8Ikbjf6ch4CgG5Qtwg6k6hS"
CATALOG_ID = os.environ.get("DRIVE_CATALOG_FOLDER_ID") or "1vEyctBT3z9F5-hFM-DeTWEsjaY2I8drb"
SCOPES = ["https://www.googleapis.com/auth/drive"]
SUPPORTED = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"}


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


def list_source_items(drive, folder_id):
    response = drive.files().list(
        q="'%s' in parents and trashed = false" % folder_id,
        pageSize=1000, fields="files(id,name,mimeType,modifiedTime,md5Checksum,size,parents)",
        orderBy="name", supportsAllDrives=True, includeItemsFromAllDrives=True,
    ).execute()
    return [item for item in response.get("files", [])
            if item.get("mimeType") != "application/vnd.google-apps.folder"]


def list_sources(drive, folder_id=FOLDER_ID):
    return [item for item in list_source_items(drive, folder_id) if item.get("mimeType") in SUPPORTED]


def ensure_processed_folder(drive, intake_id):
    intake = drive.files().get(
        fileId=intake_id, fields="id,name,parents,driveId", supportsAllDrives=True,
    ).execute()
    parents = intake.get("parents", [])
    if not parents:
        raise RuntimeError("The intake folder has no parent; cannot create its ELABORATE sibling")
    parent_id = parents[0]
    query = (
        f"'{parent_id}' in parents and trashed = false and "
        "name = 'ELABORATE' and mimeType = 'application/vnd.google-apps.folder'"
    )
    matches = drive.files().list(
        q=query, pageSize=100, fields="files(id,name,mimeType,parents)",
        supportsAllDrives=True, includeItemsFromAllDrives=True,
    ).execute().get("files", [])
    if matches:
        return matches[0]
    return drive.files().create(
        body={"name": "ELABORATE", "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]},
        fields="id,name,mimeType,parents", supportsAllDrives=True,
    ).execute()


def download(drive, item):
    from googleapiclient.http import MediaIoBaseDownload

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
        "ingredient order, botanical names, allergens and legal text. Do not guess technical values: if a required "
        "field is absent or ambiguous, return an empty value so validation blocks publication. EAN may be empty. "
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


def prepare(drive, source_id, processed_id, manifest, client, build_dir=BUILD, run_dir=None):
    """Create a validated sync plan without moving Drive files or changing remote state."""
    build_dir = Path(build_dir)
    run_dir = Path(run_dir or os.environ.get("DRIVE_RUN_DIR") or BUILD)
    run_dir.mkdir(parents=True, exist_ok=True)
    intake_items = list_source_items(drive, source_id)
    active_items = list_source_items(drive, processed_id)
    unsupported = [item for item in intake_items + active_items if item.get("mimeType") not in SUPPORTED]
    if unsupported:
        errors = [{"file": item.get("name", item.get("id", "unknown")),
                   "errors": ["Unsupported file type in a managed folder: " + item.get("mimeType", "unknown")]}
                  for item in unsupported]
        plan = {
            "status": "blocked", "changed_pending": [], "changed_active": [], "imported": {},
            "unchanged": [], "removed_source_ids": [], "removed_folders": [],
            "move_source_ids": [], "next_manifest": manifest, "active_products": {}, "errors": errors,
        }
        write_plan_files(run_dir, plan)
        return plan

    pending = intake_items
    active = active_items
    state = reconcile_sources(pending, active, manifest)
    existing = set()
    for filename in DATA_FILES:
        source = build_dir / filename
        if source.exists():
            existing.update(item["folder"] for item in json.loads(source.read_text(encoding="utf-8")))
    unchanged_folders = {
        state["next_products"][source_id].get("folder")
        for source_id in state["unchanged"]
        if state["next_products"].get(source_id, {}).get("folder")
    }

    imported, updated_entries, errors = {}, {}, []
    changed_pending = state["changed_pending"]
    changed_active = state["changed_active"]
    for item in sorted(changed_pending + changed_active, key=lambda value: value["id"]):
        try:
            product = canonicalize_product(extract(client, item, download(drive, item)), item["name"])
            validation = validate_product(product)
            if validation:
                errors.append({"file": item["name"], "errors": validation})
                continue

            folder = product["folder"]
            old_entry = manifest.get("products", {}).get(item["id"], {})
            old_folder = old_entry.get("folder")
            if folder in existing and folder != old_folder:
                errors.append({"file": item["name"], "errors": [
                    f"Product folder collision with an existing catalog product: {folder}"
                ]})
                continue
            if folder in unchanged_folders and folder != old_folder:
                errors.append({"file": item["name"], "errors": [
                    f"Product folder collision with an active supplier product: {folder}"
                ]})
                continue
            folder, collision = resolve_output_folder(product, set(), imported, unchanged_folders - {old_folder})
            if collision:
                errors.append({"file": item["name"], "errors": [collision]})
                continue
            imported[folder] = product
            updated_entries[item["id"]] = product_manifest_entry(item, folder, product["title"])
        except Exception as exc:
            errors.append({"file": item["name"], "errors": [str(exc)]})

    current_ids = {item["id"] for item in pending + active}
    removed_folders = removed_product_folders(manifest, current_ids, updated_entries)
    next_products = dict(state["next_products"])
    next_products.update(updated_entries)
    next_manifest = {
        "version": 2,
        "products": next_products,
        "legacy_folders": manifest.get("legacy_folders", []) if isinstance(manifest, dict) else [],
    }
    active_products = {}
    for entry in next_products.values():
        folder = entry.get("folder")
        if folder:
            active_products[folder] = entry.get("title", {})
    for folder, product in imported.items():
        active_products[folder] = product["title"]

    plan = {
        "status": "blocked" if errors else "ready",
        "changed_pending": changed_pending,
        "changed_active": changed_active,
        "imported": imported,
        "unchanged": state["unchanged"],
        "removed_source_ids": state["removed_source_ids"],
        "removed_folders": removed_folders,
        "move_source_ids": sorted(item["id"] for item in pending),
        "next_manifest": next_manifest,
        "active_products": active_products,
        "errors": errors,
    }
    write_plan_files(run_dir, plan)
    return plan


def write_plan_files(run_dir, plan):
    plan_path = Path(run_dir) / "drive_sync_plan.json"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    report = {
        "status": plan["status"],
        "imported": sorted(plan.get("imported", {})),
        "unchanged": len(plan.get("unchanged", [])),
        "removed": plan.get("removed_folders", []),
        "errors": plan.get("errors", []),
    }
    (Path(run_dir) / "drive_sync_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8",
    )


def main():
    from openai import OpenAI

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
    processed = ensure_processed_folder(drive, FOLDER_ID)
    previous_path = BUILD / "drive_manifest.json"
    previous = load_manifest(previous_path)
    run_dir = Path(os.environ.get("DRIVE_RUN_DIR") or os.environ.get("RUNNER_TEMP") or BUILD)
    plan = prepare(drive, FOLDER_ID, processed["id"], previous, OpenAI(), run_dir=run_dir)
    report_text = json.dumps({
        "status": plan["status"], "imported": sorted(plan["imported"]),
        "unchanged": len(plan["unchanged"]), "removed": plan["removed_folders"],
        "errors": plan["errors"],
    }, ensure_ascii=False, indent=2)
    (BUILD / "drive_sync_report.json").write_text(report_text, encoding="utf-8")
    if plan["status"] != "ready":
        print(report_text, file=sys.stderr)
        raise SystemExit("Drive import blocked; see drive_sync_report.json")

    (BUILD / "removed_products.json").write_text(
        json.dumps(plan["removed_folders"], ensure_ascii=False, indent=2), encoding="utf-8",
    )
    previous_path.write_text(json.dumps(plan["next_manifest"], ensure_ascii=False, indent=2), encoding="utf-8")
    (BUILD / "product_overrides.json").write_text(
        json.dumps(plan["imported"], ensure_ascii=False, indent=2), encoding="utf-8",
    )
    print("Drive sync ready:", len(plan["imported"]), "changed products;", len(plan["unchanged"]), "unchanged")


if __name__ == "__main__":
    main()
