import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
removed = json.loads((Path(__file__).parent / "removed_products.json").read_text(encoding="utf-8"))
for folder in removed:
    target = (ROOT / folder).resolve()
    if target.parent != ROOT.resolve() or not folder[:1].isdigit():
        raise SystemExit("Refusing to remove unsafe product folder: " + folder)
    if target.is_dir():
        shutil.rmtree(target)
        print("REMOVED", folder)
