"""Apply a validated static-site bundle to the tracked repository checkout."""
import re
import shutil
from pathlib import Path

from build_index import load_static_titles
from i18n import LANGS


PRODUCT_FOLDER = re.compile(r"^\d{2}_[A-Z0-9_]+$")
ROOT_FILES = ("index.html", "house-of-tartufo-logo.png", "vercel.json")


def _expected_product_files(folder):
    return {f"{folder}_{language}.{extension}"
            for language in LANGS for extension in ("html", "pdf")}


def _safe_folder(value, label):
    if not isinstance(value, str) or not PRODUCT_FOLDER.fullmatch(value):
        raise ValueError(f"Unsafe {label} product folder: {value!r}")
    return value


def apply_site_bundle(repo_root, bundle_root, plan, static_folders=None):
    """Copy active outputs, remove only manifest-owned removals, and return changed paths."""
    repo_root = Path(repo_root).resolve()
    bundle_root = Path(bundle_root).resolve()
    if bundle_root == repo_root or repo_root in bundle_root.parents:
        raise ValueError("site bundle must be outside the repository root")
    if not repo_root.is_dir() or not bundle_root.is_dir():
        raise ValueError("repository and site bundle roots must be existing directories")

    active = plan.get("active_products")
    manifest = plan.get("next_manifest")
    products = manifest.get("products") if isinstance(manifest, dict) else None
    if not isinstance(active, dict) or not isinstance(products, dict):
        raise ValueError("sync plan is missing active product metadata")
    active_folders = {_safe_folder(folder, "active") for folder in active}
    manifest_folders = {
        _safe_folder(entry.get("folder"), "manifest")
        for entry in products.values()
        if isinstance(entry, dict) and entry.get("folder")
    }
    if active_folders != manifest_folders:
        raise ValueError("sync plan active products do not match its next manifest")

    removed = plan.get("removed_folders", [])
    if not isinstance(removed, list):
        raise ValueError("sync plan removed_folders must be a list")
    removed_folders = {_safe_folder(folder, "removed") for folder in removed}
    if len(removed_folders) != len(removed):
        raise ValueError("sync plan contains duplicate removed product folders")
    if active_folders & removed_folders:
        raise ValueError("sync plan marks an active product for removal")

    known_static = set(load_static_titles()) if static_folders is None else set(static_folders)
    bundle_entries = list(bundle_root.iterdir())
    bundle_folders = {path.name for path in bundle_entries if path.is_dir()}
    if bundle_folders != active_folders:
        raise ValueError("bundle product folders does not match active product list")
    unexpected = {path.name for path in bundle_entries if not path.is_dir()} - set(ROOT_FILES)
    if unexpected:
        raise ValueError("bundle contains unexpected root file(s): " + ", ".join(sorted(unexpected)))
    if not (bundle_root / "index.html").is_file():
        raise ValueError("bundle is missing index.html")

    for folder in active_folders:
        source = bundle_root / folder
        if source.is_symlink() or not source.is_dir():
            raise ValueError(f"bundle product path is not a regular directory: {folder}")
        files = {path.name for path in source.iterdir() if path.is_file() and not path.is_symlink()}
        if files != _expected_product_files(folder):
            missing = sorted(_expected_product_files(folder) - files)
            extra = sorted(files - _expected_product_files(folder))
            raise ValueError(f"invalid product output set for {folder}; missing={missing}; extra={extra}")
        if any(path.is_dir() or path.is_symlink() for path in source.iterdir()):
            raise ValueError(f"bundle product folder contains nested or linked paths: {folder}")

    for folder in removed_folders:
        target = repo_root / folder
        if target.is_symlink():
            raise ValueError(f"refusing to remove linked product folder: {folder}")
        if target.exists() and not target.is_dir():
            raise ValueError(f"refusing to remove non-directory product path: {folder}")
        if target.exists() and folder not in known_static:
            # Dynamic products may be removed too, but only if the directory looks like
            # one of the generated product folders owned by the sync system.
            existing = {path.name for path in target.iterdir() if path.is_file()}
            if not existing or not existing <= _expected_product_files(folder):
                raise ValueError(f"refusing to remove an unowned product folder: {folder}")

    for folder in active_folders:
        target = repo_root / folder
        if target.is_symlink() or (target.exists() and not target.is_dir()):
            raise ValueError(f"refusing to overwrite non-directory product path: {folder}")
    for filename in ROOT_FILES:
        target = repo_root / filename
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise ValueError(f"refusing to overwrite non-file site asset: {filename}")

    changed_paths = []
    for folder in sorted(active_folders):
        shutil.copytree(bundle_root / folder, repo_root / folder, dirs_exist_ok=True)
        changed_paths.append(folder)
    for folder in sorted(removed_folders):
        target = repo_root / folder
        if target.is_dir():
            shutil.rmtree(target)
        changed_paths.append(folder)
    for filename in ROOT_FILES:
        source = bundle_root / filename
        if source.is_file():
            shutil.copy2(source, repo_root / filename)
            changed_paths.append(filename)

    return {"active_folders": sorted(active_folders), "removed_folders": sorted(removed_folders),
            "changed_paths": sorted(set(changed_paths))}


def main(argv=None):
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    if plan.get("status") != "ready":
        raise SystemExit("Cannot apply a blocked Drive sync plan")
    result = apply_site_bundle(args.repo_root, args.bundle, plan)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
