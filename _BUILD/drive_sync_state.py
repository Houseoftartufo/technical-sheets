"""Pure helpers for deterministic and incremental supplier-sheet imports."""
from copy import deepcopy
import hashlib
import json
import re

OIL_CARPACCIO = {
    "folder": "28_CARPACCIO_DI_TARTUFO_ESTIVO_IN_OLIO",
    "title": {
        "ITA": "Carpaccio di tartufo estivo in olio",
        "FR": "Carpaccio de truffe d’été à l’huile",
        "ENG": "Summer truffle carpaccio in oil",
        "NL": "Carpaccio van zomertruffel in olie",
        "DE": "Sommertrüffel-Carpaccio in Öl",
    },
}
WATER_TERMS = re.compile(r"\b(acqua|water|eau|wasser|agua|in water)\b", re.IGNORECASE)


def canonicalize_product(product, source_name):
    """Assign the known oil carpaccio its stable catalog identity without mutating input."""
    result = deepcopy(product)
    name = source_name.casefold()
    title_ita = result.get("title", {}).get("ITA", "")
    if "carpaccio" in name and "tartufo" in name and not WATER_TERMS.search(name):
        if not WATER_TERMS.search(title_ita):
            result["folder"] = OIL_CARPACCIO["folder"]
            result.setdefault("title", {}).update(OIL_CARPACCIO["title"])
    return result



def resolve_output_folder(product, existing_folders, imported_products, reserved_folders=()):
    """Choose a safe destination or block if two supplier files collide."""
    original = product["folder"]
    if original in existing_folders or original in reserved_folders:
        return None, f"Product folder collision for '{original}'; classify the supplier sheet before publishing."
    if original in imported_products:
        return None, (
            "Multiple supplier files resolve to the same product folder "
            f"'{original}'; rename or classify the supplier sheet before publishing."
        )
    return original, None


def source_fingerprint(item):
    """Stable digest for source content and extraction-relevant metadata."""
    source = {
        "md5Checksum": item.get("md5Checksum"),
        "modifiedTime": item.get("modifiedTime"),
        "name": item.get("name", ""),
        "mimeType": item.get("mimeType", ""),
        "size": item.get("size"),
    }
    return hashlib.sha256(json.dumps(source, sort_keys=True).encode("utf-8")).hexdigest()


def product_manifest_entry(item, folder, title):
    languages = ("ITA", "FR", "ENG", "NL", "DE")
    return {
        "fingerprint": source_fingerprint(item),
        "folder": folder,
        "name": item.get("name", ""),
        "title": {language: title.get(language, "") for language in languages},
    }


def unchanged_source_ids(sources, manifest):
    products = manifest.get("products", {}) if isinstance(manifest, dict) else {}
    return {
        item["id"] for item in sources
        if item["id"] in products
        and products[item["id"]].get("fingerprint") == source_fingerprint(item)
    }


def removed_product_folders(previous, current_source_ids, updated_entries=None):
    """Return stale owned folders; keep folders referenced by any active source."""
    if not isinstance(previous, dict):
        return []
    updated_entries = updated_entries or {}
    products = previous.get("products", {})
    stale = set()
    retained = set()
    for source_id, entry in products.items():
        old_folder = entry.get("folder")
        if source_id not in current_source_ids:
            if old_folder:
                stale.add(old_folder)
            continue
        new_entry = updated_entries.get(source_id, entry)
        new_folder = new_entry.get("folder")
        if new_folder:
            retained.add(new_folder)
        if old_folder and old_folder != new_folder:
            stale.add(old_folder)
    return sorted(stale - retained)


def reconcile_sources(pending_sources, active_sources, manifest):
    """Reconcile the intake queue and active originals without treating a move as deletion."""
    pending = {item["id"]: item for item in pending_sources}
    active = {item["id"]: item for item in active_sources}
    overlapping = set(pending) & set(active)
    if overlapping:
        raise ValueError("Drive source IDs appear in both intake and processed folders: "
                         + ", ".join(sorted(overlapping)))

    previous = manifest.get("products", {}) if isinstance(manifest, dict) else {}
    current_ids = set(pending) | set(active)
    changed_pending, changed_active, unchanged = [], [], []
    for source_id in sorted(current_ids):
        item = pending.get(source_id) or active[source_id]
        entry = previous.get(source_id, {})
        if entry.get("fingerprint") == source_fingerprint(item):
            unchanged.append(source_id)
        elif source_id in pending:
            changed_pending.append(item)
        else:
            changed_active.append(item)

    removed_source_ids = sorted(set(previous) - current_ids)
    next_products = {source_id: previous[source_id] for source_id in sorted(current_ids)
                     if source_id in previous}
    removed_folders = removed_product_folders(manifest, current_ids)
    return {
        "changed_pending": changed_pending,
        "changed_active": changed_active,
        "unchanged": unchanged,
        "removed_source_ids": removed_source_ids,
        "removed_folders": removed_folders,
        "next_products": next_products,
    }


def load_manifest(path):
    if not path.exists():
        return {"version": 2, "products": {}, "legacy_folders": []}
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, list):
        return {"version": 2, "products": {}, "legacy_folders": sorted(set(value))}
    if not isinstance(value, dict) or not isinstance(value.get("products", {}), dict):
        raise ValueError("drive_manifest.json has an unsupported format")
    if value.get("version", 1) not in (1, 2):
        raise ValueError("drive_manifest.json has an unsupported version")
    return {"version": 2, "products": value.get("products", {}),
            "legacy_folders": value.get("legacy_folders", [])}
