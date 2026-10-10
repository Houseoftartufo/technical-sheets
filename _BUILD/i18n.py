# -*- coding: utf-8 -*-
"""Load the unchanged source data and add language overlays at runtime."""

from copy import deepcopy
import json
from pathlib import Path

from german import DE_TRANSLATIONS


LEGACY_LANGS = ("ITA", "FR", "ENG", "NL")
LANGS = (*LEGACY_LANGS, "DE")
DATA_FILES = ("p01.json", "p02.json", "blockA.json", "blockB.json", "blockC.json", "blockD.json", "blockE.json")
LOCALIZED_PATHS = (
    ("title",),
    ("general", "typology"),
    ("general", "shelf"),
    ("general", "packaging"),
    ("general", "labelling"),
    ("general", "gmo"),
    ("ingredients", "ingredients"),
    ("ingredients", "allergens"),
    ("storage", "instructions"),
    ("storage", "method"),
    ("characteristics", "chemical"),
    ("characteristics", "micro"),
)
OPTIONAL_LOCALIZED_PATHS = (("characteristics", "chemical"), ("characteristics", "micro"))
REQUIRED_LOCALIZED_PATHS = tuple(path for path in LOCALIZED_PATHS if path not in OPTIONAL_LOCALIZED_PATHS)


def _get(mapping, path):
    value = mapping
    for key in path:
        value = value[key]
    return value


def _set(mapping, path, value):
    target = mapping
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value


def add_german(product):
    product = deepcopy(product)
    required_complete = all(
        isinstance(_get(product, path), dict)
        and all(language in _get(product, path) for language in LANGS)
        for path in REQUIRED_LOCALIZED_PATHS
    )
    optional_complete = all(
        not _has_path(product, path)
        or (
            isinstance(_get(product, path), dict)
            and all(language in _get(product, path) for language in LANGS)
        )
        for path in OPTIONAL_LOCALIZED_PATHS
    )
    if required_complete and optional_complete:
        return product

    folder = product["folder"]
    if folder not in DE_TRANSLATIONS:
        raise ValueError(f"Missing German translation for {folder}")
    translation = DE_TRANSLATIONS[folder]

    for path in LOCALIZED_PATHS:
        try:
            current = _get(product, path)
        except (KeyError, TypeError):
            if path in OPTIONAL_LOCALIZED_PATHS:
                continue
            raise
        german = _get(translation, path)
        if isinstance(current, dict):
            current["DE"] = german
        else:
            localized = {lang: current for lang in LEGACY_LANGS}
            localized["DE"] = german
            _set(product, path, localized)
    return product


def _has_path(mapping, path):
    try:
        _get(mapping, path)
        return True
    except (KeyError, TypeError):
        return False


def load_products_file(path):
    path = Path(path)
    products = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(products, dict):
        products = list(products.values())
    return [add_german(product) for product in products]


def load_all_products(build_dir):
    build_dir = Path(build_dir)
    products = []
    for filename in DATA_FILES:
        products.extend(load_products_file(build_dir / filename))
    base_folders = {product["folder"] for product in products}
    if set(DE_TRANSLATIONS) != base_folders:
        raise ValueError("German translation set does not match the 27 source products")

    overrides_path = build_dir / "product_overrides.json"
    if overrides_path.exists():
        overrides = json.loads(overrides_path.read_text(encoding="utf-8"))
        if not isinstance(overrides, dict):
            raise ValueError("product_overrides.json must contain an object keyed by product folder")
        positions = {product["folder"]: index for index, product in enumerate(products)}
        for folder, product in overrides.items():
            if product.get("folder") != folder:
                raise ValueError(f"Product override key does not match its folder: {folder}")
            product = add_german(product)
            if folder in positions:
                products[positions[folder]] = product
            else:
                positions[folder] = len(products)
                products.append(product)

    removed_path = build_dir / "removed_products.json"
    if removed_path.exists():
        removed = json.loads(removed_path.read_text(encoding="utf-8"))
        if not isinstance(removed, list) or not all(isinstance(folder, str) for folder in removed):
            raise ValueError("removed_products.json must be a list of product folder names")
        removed_set = set(removed)
        products = [product for product in products if product["folder"] not in removed_set]
    return products


def localized(value, lang):
    return value[lang] if isinstance(value, dict) else value
