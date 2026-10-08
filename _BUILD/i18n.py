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
    folder = product["folder"]
    if folder not in DE_TRANSLATIONS:
        raise ValueError(f"Missing German translation for {folder}")
    translation = DE_TRANSLATIONS[folder]

    for path in LOCALIZED_PATHS:
        current = _get(product, path)
        german = _get(translation, path)
        if isinstance(current, dict):
            current["DE"] = german
        else:
            localized = {lang: current for lang in LEGACY_LANGS}
            localized["DE"] = german
            _set(product, path, localized)
    return product


def load_products_file(path):
    path = Path(path)
    products = json.loads(path.read_text(encoding="utf-8"))
    return [add_german(product) for product in products]


def load_all_products(build_dir):
    build_dir = Path(build_dir)
    products = []
    for filename in DATA_FILES:
        products.extend(load_products_file(build_dir / filename))
    if set(DE_TRANSLATIONS) != {product["folder"] for product in products}:
        raise ValueError("German translation set does not match the 27 source products")
    return products


def localized(value, lang):
    return value[lang] if isinstance(value, dict) else value
