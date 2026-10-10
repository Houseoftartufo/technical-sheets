"""Deterministic, non-destructive bootstrap for the supplier source catalogue."""
import json
from pathlib import Path

from drive_sync_state import OIL_CARPACCIO, canonical_managed_name, product_manifest_entry


def load_baseline_mapping(path):
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("version") != 1 or not isinstance(value.get("sources"), dict):
        raise ValueError("Drive baseline mapping has an unsupported format")
    return value


def seed_baseline_manifest(active_items, mapping, static_titles, previous_manifest=None):
    """Map existing supplier originals without extracting legacy products or scheduling deletions."""
    source_mapping = mapping.get("sources", mapping) if isinstance(mapping, dict) else None
    if not isinstance(source_mapping, dict) or not source_mapping:
        raise ValueError("Drive baseline source mapping is empty or invalid")
    if len(set(source_mapping.values())) != len(source_mapping):
        raise ValueError("duplicate mapped product folder in baseline mapping")

    expected_names = set(source_mapping)
    matched = {}
    unexpected = []
    duplicates = []
    ids = set()
    for item in active_items:
        current_name = item.get("name", "")
        candidates = [
            original for original, folder in source_mapping.items()
            if current_name in {original, f"{folder}__{Path(original).name}"}
        ]
        if not candidates:
            unexpected.append(current_name)
            continue
        if len(candidates) != 1:
            raise ValueError(f"ambiguous source name in ELABORATE: {current_name}")
        original = candidates[0]
        if original in matched:
            duplicates.append(original)
            continue
        source_id = item.get("id")
        if not source_id or source_id in ids:
            raise ValueError("ELABORATE contains a source with a missing or duplicate Drive ID")
        ids.add(source_id)
        matched[original] = {**item, "original_name": original}
    if duplicates:
        raise ValueError("duplicate source name(s) in ELABORATE: " + ", ".join(sorted(duplicates)))
    missing = sorted(expected_names - set(matched))
    if missing:
        raise ValueError("missing source(s) from ELABORATE: " + ", ".join(missing))
    if unexpected:
        raise ValueError("unexpected source(s) in ELABORATE: " + ", ".join(sorted(unexpected)))

    oil_name = "Carpaccio di tartufo estivo - scheda tecnica.pdf"
    mapped_dynamic = {name: folder for name, folder in source_mapping.items() if folder == OIL_CARPACCIO["folder"]}
    if mapped_dynamic != {oil_name: OIL_CARPACCIO["folder"]}:
        raise ValueError("baseline mapping must contain only the known oil carpaccio as the new product")
    unknown_static = sorted({folder for folder in source_mapping.values() if folder != OIL_CARPACCIO["folder"]} - set(static_titles))
    if unknown_static:
        raise ValueError("mapped product folder(s) not present in static catalog: " + ", ".join(unknown_static))
    mapped_static = {name: folder for name, folder in source_mapping.items() if folder != OIL_CARPACCIO["folder"]}
    missing_folders = sorted(set(static_titles) - set(mapped_static.values()))
    if missing_folders:
        raise ValueError("baseline mapping is missing static catalog folder(s): " + ", ".join(missing_folders))

    products = {}
    for name, folder in mapped_static.items():
        item = matched[name]
        products[item["id"]] = product_manifest_entry(item, folder, static_titles[folder])
    new_sources = []
    for name, folder in mapped_dynamic.items():
        new_sources.append({**matched[name], "folder": folder,
                            "managed_name": canonical_managed_name(folder, matched[name]["original_name"])})
    associations = [
        {"id": matched[name]["id"], "source_name": name, "folder": folder}
        for name, folder in sorted(source_mapping.items())
    ]
    previous_manifest = previous_manifest if isinstance(previous_manifest, dict) else {}
    manifest = {
        "version": 2,
        "source_catalog_version": 1,
        "products": dict(sorted(products.items())),
        "legacy_folders": sorted(set(previous_manifest.get("legacy_folders", []))),
    }
    return {"manifest": manifest, "new_sources": new_sources, "associations": associations}
