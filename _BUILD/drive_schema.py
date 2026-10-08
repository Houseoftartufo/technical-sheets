LANGS = ("ITA", "FR", "ENG", "NL", "DE")
LOCALIZED_FIELDS = (
    ("title",),
    ("general", "typology"), ("general", "shelf"), ("general", "packaging"),
    ("general", "labelling"), ("general", "gmo"),
    ("ingredients", "ingredients"), ("ingredients", "allergens"),
    ("storage", "instructions"), ("storage", "method"),
    ("characteristics", "chemical"), ("characteristics", "micro"),
)

REQUIRED_PATHS = LOCALIZED_FIELDS + (
    ("folder",), ("general", "ean"), ("nutrition",),
)


def get_path(value, path):
    for key in path:
        value = value[key]
    return value


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
        except (KeyError, TypeError):
            pass
    return errors
