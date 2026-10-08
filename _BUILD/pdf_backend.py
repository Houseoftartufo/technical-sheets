import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def _find_chromium():
    candidates = [
        os.environ.get("PDF_BROWSER"),
        shutil.which("chrome"),
        shutil.which("chromium"),
        shutil.which("msedge"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate)
    return None


def _write_with_chromium(html, output_path, browser):
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="hot-pdf-") as temp_dir:
        temp_dir = Path(temp_dir)
        html_path = temp_dir / "sheet.html"
        html_path.write_text(html, encoding="utf-8")
        result = subprocess.run(
            [
                str(browser),
                "--headless=new",
                "--disable-gpu",
                "--no-pdf-header-footer",
                f"--user-data-dir={temp_dir / 'profile'}",
                f"--print-to-pdf={output_path}",
                html_path.as_uri(),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    if result.returncode or not output_path.is_file():
        raise RuntimeError(f"Chromium PDF generation failed: {result.stderr.strip()}")


def write_pdf(html, output_path):
    if os.name == "nt":
        browser = _find_chromium()
        if browser is not None:
            _write_with_chromium(html, output_path, browser)
            return
    try:
        from weasyprint import HTML
    except (ImportError, OSError):
        browser = _find_chromium()
        if browser is None:
            raise RuntimeError(
                "PDF generation requires WeasyPrint with its native libraries or a Chromium-based browser"
            )
        _write_with_chromium(html, output_path, browser)
    else:
        HTML(string=html).write_pdf(output_path)
