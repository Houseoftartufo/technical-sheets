"""Import supplier PDFs/DOCX files from Drive into the existing catalog engine.

The Drive folder is an input queue. Generated product records are stored in
product_overrides.json and are rendered by the same engine.py/build_index.py.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from drive_schema import LANGS, normalize_optional_fields, validate_product
from drive_sync_state import (
    canonicalize_product, load_manifest, product_manifest_entry,
    reconcile_sources, removed_product_folders, resolve_output_folder, source_fingerprint,
)
from drive_bootstrap import load_baseline_mapping, seed_baseline_manifest
from i18n import DATA_FILES

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "_BUILD"
FOLDER_ID = os.environ.get("DRIVE_SOURCE_FOLDER_ID") or "1Y1qgl2rih8Ikbjf6ch4CgG5Qtwg6k6hS"
CATALOG_ID = os.environ.get("DRIVE_CATALOG_FOLDER_ID") or "1vEyctBT3z9F5-hFM-DeTWEsjaY2I8drb"
PROCESSED_FOLDER_ID = os.environ.get("DRIVE_PROCESSED_FOLDER_ID")
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
    items = []
    page_token = None
    while True:
        response = drive.files().list(
            q="'%s' in parents and trashed = false" % folder_id,
            pageSize=1000, pageToken=page_token,
            fields="nextPageToken,files(id,name,mimeType,modifiedTime,md5Checksum,size,parents)",
            orderBy="name", supportsAllDrives=True, includeItemsFromAllDrives=True,
        ).execute()
        items.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return [item for item in items if item.get("mimeType") != "application/vnd.google-apps.folder"]


def list_sources(drive, folder_id=FOLDER_ID):
    return [item for item in list_source_items(drive, folder_id) if item.get("mimeType") in SUPPORTED]


def ensure_processed_folder(drive, intake_id, processed_folder_id=None):
    if processed_folder_id:
        processed = drive.files().get(
            fileId=processed_folder_id, fields="id,name,mimeType,parents,driveId", supportsAllDrives=True,
        ).execute()
        if processed.get("mimeType") != "application/vnd.google-apps.folder":
            raise RuntimeError(f"Configured DRIVE_PROCESSED_FOLDER_ID {processed_folder_id} must be a Drive folder")
        return processed
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
    filename = Path(item.get("name", "supplier.pdf")).name
    mime_type = item.get("mimeType")
    if mime_type in {"application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"}:
        with tempfile.TemporaryDirectory(prefix="supplier-word-") as temp:
            temp_path = Path(temp)
            source_path = temp_path / filename
            source_path.write_bytes(content)
            converted_path = temp_path / (source_path.stem + ".pdf")
            result = subprocess.run(
                ["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", str(temp_path), str(source_path)],
                capture_output=True, text=True, check=True, timeout=180,
            )
            if not converted_path.is_file():
                raise RuntimeError("Word-to-PDF conversion did not create an output file: " + result.stderr[-500:])
            upload_name, upload_content = converted_path.name, converted_path.read_bytes()
    else:
        upload_name, upload_content = filename, content
    uploaded = client.files.create(file=(upload_name, upload_content), purpose="user_data")
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
                **{
                    name: {"type": "string"}
                    for name in ("energy", "fat", "sat", "carb", "sugar", "protein", "salt")
                },
                "fibre": {"type": ["string", "null"]},
            }),
            "characteristics": object_schema({
                "chemical": {"anyOf": [localized_schema(), {"type": "null"}]},
                "micro": {"anyOf": [localized_schema(), {"type": "null"}]},
            }),
        },
        "required": ["folder", "title", "general", "ingredients", "storage", "nutrition", "characteristics"],
    }
    instruction = (
        "Extract this supplier technical sheet into the supplied JSON schema. "
        "Translate every localized field into ITA, FR, ENG, NL, DE. Preserve exact numbers, units, percentages, "
        "ingredient order, botanical names, allergens and legal text. Do not guess technical values: if a required "
        "required field is absent or ambiguous, return an empty value so validation blocks publication. EAN may be empty. "
        "Dietary fibre, chemical characteristics, and microbiological characteristics are optional: if the source does not "
        "state them, return null and do not infer or copy them from a different product. Present optional characteristics "
        "must be translated completely into every language. Use the product folder identifier in uppercase with underscores."
    )
    try:
        response = client.responses.create(
            model=os.environ.get("OPENAI_IMPORT_MODEL", "gpt-4.1"),
            input=[{"role": "user", "content": [
                {"type": "input_file", "file_id": uploaded.id, "detail": "high"},
                {"type": "input_text", "text": instruction},
            ]}],
            text={"format": {"type": "json_schema", "name": "technical_sheet", "strict": True, "schema": schema}},
        )
        return json.loads(response.output_text)
    finally:
        client.files.delete(uploaded.id)


def prepare(drive, source_id, processed_id, manifest, client, build_dir=BUILD, run_dir=None, bootstrap_mapping=None):
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
            "move_source_ids": [], "rename_sources": [], "duplicate_sources": [], "bootstrap": False,
            "source_mapping": [], "source_folder_id": source_id, "processed_folder_id": processed_id,
            "next_manifest": manifest, "active_products": {}, "errors": errors,
        }
        write_plan_files(run_dir, plan)
        return plan

    bootstrap = None
    if bootstrap_mapping is not None:
        try:
            from build_index import load_static_titles
            bootstrap = seed_baseline_manifest(active_items, bootstrap_mapping, load_static_titles(build_dir), manifest)
            manifest = bootstrap["manifest"]
            baseline_by_id = {item["id"]: item for item in bootstrap["new_sources"]}
            active_items = [
                {**item, "original_name": baseline_by_id[item["id"]]["original_name"]}
                if item["id"] in baseline_by_id else item
                for item in active_items
            ]
        except Exception as exc:
            plan = {
                "status": "blocked", "changed_pending": [], "changed_active": [], "imported": {},
                "unchanged": [], "removed_source_ids": [], "removed_folders": [],
                "move_source_ids": [], "rename_sources": [], "duplicate_sources": [], "bootstrap": True,
                "source_mapping": [], "source_folder_id": source_id, "processed_folder_id": processed_id,
                "next_manifest": manifest, "active_products": {},
                "errors": [{"file": "ELABORATE baseline", "errors": [str(exc)]}],
            }
            write_plan_files(run_dir, plan)
            return plan

    active_checksums = {item.get("md5Checksum") for item in active_items if item.get("md5Checksum")}
    duplicate_pending = [item for item in intake_items
                         if item.get("md5Checksum") and item.get("md5Checksum") in active_checksums]
    duplicate_ids = {item["id"] for item in duplicate_pending}
    pending = [item for item in intake_items if item["id"] not in duplicate_ids]
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
            product = normalize_optional_fields(
                canonicalize_product(extract(client, item, download(drive, item)), item["name"])
            )
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
            original_name = old_entry.get("original_name") or old_entry.get("name") or item.get("original_name") or item.get("name", "")
            updated_entries[item["id"]] = product_manifest_entry(
                {**item, "original_name": original_name}, folder, product["title"]
            )
        except Exception as exc:
            errors.append({"file": item["name"], "errors": [str(exc)]})

    current_items = pending + active
    current_ids = {item["id"] for item in current_items}
    removed_folders = removed_product_folders(manifest, current_ids, updated_entries)
    next_products = dict(state["next_products"])
    next_products.update(updated_entries)
    next_manifest = {
        "version": 2,
        "source_catalog_version": manifest.get("source_catalog_version", 1) if isinstance(manifest, dict) else 1,
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

    next_by_id = next_products
    rename_sources = []
    for item in current_items:
        entry = next_by_id.get(item["id"])
        managed_name = entry.get("managed_name") if entry else None
        if managed_name and item.get("name") != managed_name:
            rename_sources.append({"id": item["id"], "from_name": item.get("name", ""), "to_name": managed_name})
    plan = {
        "status": "blocked" if errors else "ready",
        "bootstrap": bool(bootstrap),
        "source_mapping": (bootstrap or {}).get("associations", []),
        "rename_sources": sorted(rename_sources, key=lambda item: item["id"]),
        "duplicate_sources": [{"id": item["id"], "name": item["name"], "reason": "same content checksum already exists in ELABORATE"} for item in duplicate_pending],
        "changed_pending": changed_pending,
        "changed_active": changed_active,
        "imported": imported,
        "unchanged": state["unchanged"],
        "removed_source_ids": state["removed_source_ids"],
        "removed_folders": removed_folders,
        "move_source_ids": sorted(item["id"] for item in pending) if not errors else [],
        "source_folder_id": source_id, "processed_folder_id": processed_id,
        "next_manifest": next_manifest,
        "active_products": active_products,
        "errors": errors,
    }
    write_plan_files(run_dir, plan)
    return plan


def load_manifest_bytes(data):
    value = json.loads(data.decode("utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("products", {}), dict):
        raise ValueError("Drive manifest has an unsupported format")
    if value.get("version", 1) not in (1, 2):
        raise ValueError("Drive manifest has an unsupported version")
    manifest = {"version": 2, "products": value.get("products", {}),
                "legacy_folders": value.get("legacy_folders", [])}
    if value.get("source_catalog_version") is not None:
        manifest["source_catalog_version"] = value["source_catalog_version"]
    return manifest


def write_plan_files(run_dir, plan):
    plan_path = Path(run_dir) / "drive_sync_plan.json"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    report = {
        "status": plan["status"],
        "bootstrap": plan.get("bootstrap", False),
        "imported": sorted(plan.get("imported", {})),
        "unchanged": len(plan.get("unchanged", [])),
        "removed": plan.get("removed_folders", []),
        "rename_planned": plan.get("rename_sources", []),
        "source_mapping": plan.get("source_mapping", []),
        "duplicates": plan.get("duplicate_sources", []),
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
    if not PROCESSED_FOLDER_ID:
        raise SystemExit("DRIVE_PROCESSED_FOLDER_ID must point to the existing ELABORATE folder; no folder will be created automatically")
    processed = ensure_processed_folder(drive, FOLDER_ID, PROCESSED_FOLDER_ID)
    run_dir = Path(os.environ.get("DRIVE_RUN_DIR") or os.environ.get("RUNNER_TEMP") or BUILD)
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_matches = drive.files().list(
        q=f"'{CATALOG_ID}' in parents and trashed = false and name = '.technical-sheets-manifest.json'",
        pageSize=10, fields="files(id,name)", supportsAllDrives=True, includeItemsFromAllDrives=True,
    ).execute().get("files", [])
    if len(manifest_matches) > 1:
        raise SystemExit("Multiple Drive sync manifests found; refusing to choose one")
    manifest_file_id = manifest_matches[0]["id"] if manifest_matches else None
    if manifest_file_id:
        from publish_drive import download_drive_file
        previous = load_manifest_bytes(download_drive_file(drive, manifest_matches[0]))
        bootstrap_mapping = None
    else:
        previous = load_manifest(BUILD / "drive_manifest.json")
    bootstrap_mapping = (None if previous.get("source_catalog_version") == 1
                         else load_baseline_mapping(BUILD / "drive_baseline_mapping.json"))
    (run_dir / "manifest_file_id.txt").write_text(manifest_file_id or "", encoding="utf-8")
    plan = prepare(drive, FOLDER_ID, processed["id"], previous, OpenAI(), run_dir=run_dir,
                   build_dir=BUILD, bootstrap_mapping=bootstrap_mapping)
    (run_dir / "product_overrides.json").write_text(
        json.dumps(plan.get("imported", {}), ensure_ascii=False, indent=2), encoding="utf-8",
    )
    report_text = json.dumps({
        "status": plan["status"], "bootstrap": plan["bootstrap"],
        "imported": sorted(plan["imported"]), "unchanged": len(plan["unchanged"]),
        "removed": plan["removed_folders"], "rename_planned": plan["rename_sources"],
        "source_mapping": plan["source_mapping"], "duplicates": plan["duplicate_sources"],
        "errors": plan["errors"],
    }, ensure_ascii=False, indent=2)
    (run_dir / "drive_sync_report.json").write_text(report_text, encoding="utf-8")
    if plan["status"] != "ready":
        print(report_text, file=sys.stderr)
        raise SystemExit("Drive import blocked; see the uploaded drive-sync-report artifact")
    print("Drive sync ready:", len(plan["imported"]), "changed products;", len(plan["unchanged"]), "unchanged")


if __name__ == "__main__":
    main()
