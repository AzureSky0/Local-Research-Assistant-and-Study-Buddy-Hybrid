"""Render the public project overview (docs/showcase/brochure.html) to a PDF.

Usage (from the project root):

    python scripts/build_showcase_pdf.py

Uses Google Chrome or Microsoft Edge in headless mode, so the fonts
(IBM Plex, from Google Fonts) need an internet connection. The
screenshots in docs/showcase/images come from the real app.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "docs" / "showcase" / "brochure.html"
OUTPUT = ROOT / "docs" / "showcase" / "Loci-overview.pdf"

BROWSERS = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
]


def main() -> None:
    browser = next((path for path in BROWSERS if path.exists()), None)
    if browser is None:
        sys.exit("Chrome or Edge is needed to render the PDF.")

    with tempfile.TemporaryDirectory() as profile:
        subprocess.run(
            [
                str(browser),
                "--headless=new",
                "--disable-gpu",
                "--no-pdf-header-footer",
                # Give web fonts time to load before printing.
                "--virtual-time-budget=15000",
                f"--user-data-dir={profile}",
                f"--print-to-pdf={OUTPUT}",
                SOURCE.as_uri(),
            ],
            check=True,
            capture_output=True,
        )

    print(f"Written {OUTPUT} ({OUTPUT.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
