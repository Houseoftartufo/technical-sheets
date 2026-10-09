from copy import deepcopy

LANGS = ("ITA", "FR", "ENG", "NL", "DE")
LOCALIZED_FIELDS = (
    ("title",),
    ("general", "typology"), ("general", "shelf"), ("general", "packaging"),
    ("general", "labelling"), ("general", "gmo"),
    ("ingredients", "ingredients"), ("ingredients", "allergens"),
    ("storage", "instructions"), ("storage", "method"),
)
OPTIONAL_LOCALIZED_FIELDS = (("characteristics", "chemical"), ("characteristics", "micro"))
REQUIRED_NUTRIENTS = ("energy", "fat", "sat", "carb", "sugar", "protein", "salt")

REQUIRED_PATHS = LOCALIZED_FIELDS + (
    ("folder",), ("general", "ean"), ("nutrition",),
)


def get_path(value, path):
    for key in path:
        value = value[key]
    return value


def normalize_optional_fields(product):
    """Drop optional source fields that are absent, without inventing replacement values."""
    result = deepcopy(product)
    nutrition = result.get("nutrition")
    if isinstance(nutrition, dict) and not str(nutrition.get("fibre") or "").strip():
        nutrition.pop("fibre", None)

    characteristics = result.get("characteristics")
    if isinstance(characteristics, dict):
        for name in ("chemical", "micro"):
            values = characteristics.get(name)
            if values is None or (
                isinstance(values, dict)
                and all(not str(value or "").strip() for value in values.values())
            ):
                characteristics.pop(name, None)
        if not characteristics:
            result.pop("characteristics", None)
    return result


def validate_product(product):
    errors = []
    folder = product.get("folder", "")
    if not isinstance(folder, str) or not folder or any(c in folder for c in "\\/:*?\"<>|"):
        errors.append("folder must be a safe non-empty product identifier")
    for path in REQUIRED_PATHS:
        try:
            value = get_path(product, path)
        except (KeyError, TypeError):
            errors.append("missing field: " + ".".join(path))
            continue
        if path != ("nutrition",) and not isinstance(value, (str, dict)):
            errors.append("invalid field: " + ".".join(path))
    for path in LOCALIZED_FIELDS:
        try:
            values = get_path(product, path)
            if not isinstance(values, dict) or any(lang not in values for lang in LANGS):
                errors.append("missing language in: " + ".".join(path))
                continue
            for language in LANGS:
                value = values[language]
                if not isinstance(value, str) or not value.strip():
                    errors.append("missing required value: " + ".".join(path) + "." + language)
        except (KeyError, TypeError):
            pass
    nutrition = product.get("nutrition")
    if not isinstance(nutrition, dict):
        errors.append("invalid field: nutrition")
    else:
        for name in REQUIRED_NUTRIENTS:
            value = nutrition.get(name)
            if not isinstance(value, str) or not value.strip():
                errors.append("missing required value: nutrition." + name)
        if "fibre" in nutrition and (not isinstance(nutrition["fibre"], str) or not nutrition["fibre"].strip()):
            errors.append("invalid optional value: nutrition.fibre")

    characteristics = product.get("characteristics", {})
    if not isinstance(characteristics, dict):
        errors.append("invalid field: characteristics")
    else:
        for path in OPTIONAL_LOCALIZED_FIELDS:
            key = path[-1]
            if key not in characteristics:
                continue
            values = characteristics[key]
            if not isinstance(values, dict) or any(lang not in values for lang in LANGS):
                errors.append("missing language in: " + ".".join(path))
                continue
            for language in LANGS:
                value = values[language]
                if not isinstance(value, str) or not value.strip():
                    errors.append("missing optional translation: " + ".".join(path) + "." + language)
    return errors
