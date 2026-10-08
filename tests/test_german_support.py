import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "_BUILD"
PYTHON = sys.executable


class GermanSupportTests(unittest.TestCase):
    def test_block_generators_write_next_to_their_scripts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_build = Path(temp_dir) / "_BUILD"
            temp_build.mkdir()
            shutil.copy2(BUILD / "common.py", temp_build / "common.py")
            for name in ("blockA", "blockB", "blockC", "blockD", "blockE"):
                shutil.copy2(BUILD / f"{name}.py", temp_build / f"{name}.py")
                result = subprocess.run(
                    [PYTHON, str(temp_build / f"{name}.py")],
                    cwd=temp_build,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                data = json.loads((temp_build / f"{name}.json").read_text(encoding="utf-8"))
                self.assertEqual(len(data), 5)

    def test_index_builder_adds_german_selector_search_and_links(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "index.html"
            result = subprocess.run(
                [PYTHON, str(BUILD / "build_index.py"), "--output", str(output)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")
            html = output.read_text(encoding="utf-8")
            self.assertIn('<button data-l="DE">DE</button>', html)
            self.assertIn('data-de="Balsamico-Essig aus Modena mit Trüffelaroma"', html)
            self.assertIn("Produkt suchen...", html)
            self.assertEqual(html.count("_DE.pdf"), 27)
            self.assertIn('<button data-l="ITA" class="active">ITA</button>', html)
            self.assertNotIn('target="_blank"', html)

    def test_engine_generates_only_requested_german_artifacts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [
                    PYTHON,
                    str(BUILD / "engine.py"),
                    str(BUILD / "p01.json"),
                    temp_dir,
                    "06/06/2026",
                    "DE",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")
            self.assertNotIn("WeasyPrint could not import", result.stdout)

            folder = Path(temp_dir) / "01_ACETO_BALSAMICO_SPRAY"
            html_path = folder / "01_ACETO_BALSAMICO_SPRAY_DE.html"
            pdf_path = folder / "01_ACETO_BALSAMICO_SPRAY_DE.pdf"
            self.assertTrue(html_path.is_file())
            self.assertTrue(pdf_path.is_file())
            self.assertEqual(sorted(path.suffix for path in folder.iterdir()), [".html", ".pdf"])

            html = html_path.read_text(encoding="utf-8")
            self.assertIn('<html lang="de">', html)
            self.assertIn("TECHNISCHES PRODUKTDATENBLATT", html)
            self.assertIn("Aktualisiert: 06/06/2026", html)

    def test_engine_defaults_to_all_five_languages(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [
                    PYTHON,
                    str(BUILD / "engine.py"),
                    str(BUILD / "p01.json"),
                    temp_dir,
                    "06/06/2026",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            folder = Path(temp_dir) / "01_ACETO_BALSAMICO_SPRAY"
            expected = {
                f"01_ACETO_BALSAMICO_SPRAY_{lang}.{suffix}"
                for lang in ("ITA", "FR", "ENG", "NL", "DE")
                for suffix in ("html", "pdf")
            }
            self.assertEqual({path.name for path in folder.iterdir()}, expected)

    def test_every_product_has_complete_german_copy(self):
        result = subprocess.run(
            [
                PYTHON,
                "-c",
                (
                    "import json, sys; "
                    f"sys.path.insert(0, {str(BUILD)!r}); "
                    "from i18n import LOCALIZED_PATHS, load_all_products; "
                    f"print(json.dumps([LOCALIZED_PATHS, load_all_products({str(BUILD)!r})]))"
                ),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        paths, products = json.loads(result.stdout)
        self.assertEqual(len(products), 27)
        self.assertEqual(len({product["folder"] for product in products}), 27)

        for product in products:
            for path in paths:
                value = product
                for key in path:
                    value = value[key]
                self.assertIn("DE", value, f"{product['folder']}: {'.'.join(path)}")
                self.assertTrue(value["DE"].strip(), f"{product['folder']}: {'.'.join(path)}")


if __name__ == "__main__":
    unittest.main()
