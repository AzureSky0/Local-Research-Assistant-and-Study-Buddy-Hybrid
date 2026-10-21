"""Build the Windows app for testers: dist/Loci/Loci.exe and a zip to share.

Usage (from the project root, inside the virtual environment):

    pip install -r requirements.txt   # includes pyinstaller and pip-licenses
    python scripts/build_windows.py

Testers unzip the folder and double-click Loci.exe; no Python needed.

The package gets a `licenses` folder: Loci's licence and extension
exception, the third-party notices, the full licence text of every bundled
component (collected with pip-licenses), and where to get the source code,
as the AGPL and the bundled components' licences require.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.constants import APP_NAME, APP_VERSION  # noqa: E402

SPEC = ROOT / "packaging" / "loci.spec"
DIST = ROOT / "dist"
REPOSITORY = "https://github.com/AzureSky0/Local-Research-Assistant-and-Study-Buddy-Hybrid"

# Python packages bundled in the Windows build (see THIRD_PARTY_NOTICES.md).
BUNDLED_PACKAGES = [
    "PySide6", "PySide6_Essentials", "PySide6_Addons", "shiboken6", "PyMuPDF", "SQLAlchemy",
    "alembic", "Mako", "MarkupSafe", "greenlet", "sqlite-vec", "fastembed", "onnxruntime",
    "tokenizers", "py_rust_stemmers", "mmh3", "huggingface_hub", "hf_xet", "httpx", "httpcore",
    "h11", "anyio", "idna", "certifi", "requests", "numpy", "pillow", "psutil", "platformdirs",
    "pydantic", "pydantic_core", "pydantic-settings", "annotated-types", "typing_extensions",
    "tqdm", "loguru", "PyYAML", "filelock", "fsspec", "colorama",
]


def main() -> None:
    subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", str(SPEC)],
        cwd=ROOT,
        check=True,
    )

    app_folder = DIST / APP_NAME
    add_licenses(app_folder / "licenses")

    archive = shutil.make_archive(
        str(DIST / f"{APP_NAME}-{APP_VERSION}-windows"), "zip", DIST, APP_NAME
    )

    size_mb = sum(f.stat().st_size for f in app_folder.rglob("*") if f.is_file()) / 1e6
    print(f"\nApp folder: {app_folder} ({size_mb:.0f} MB)")
    print(f"Zip to share: {archive} ({Path(archive).stat().st_size / 1e6:.0f} MB)")


def add_licenses(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)

    for name in ("LICENSE", "LICENSE-EXTENSION-EXCEPTION.md", "THIRD_PARTY_NOTICES.md"):
        shutil.copy2(ROOT / name, folder / name)

    # Texts some packages do not ship in their metadata (Qt's LGPL, sqlite-vec).
    for text in (ROOT / "packaging" / "licenses").glob("*.txt"):
        shutil.copy2(text, folder / text.name)

    collected_file = folder / "_collected.txt"
    subprocess.run(
        [
            sys.executable, "-m", "piplicenses", "--packages", *BUNDLED_PACKAGES,
            "--with-authors", "--with-urls", "--with-license-file", "--no-license-path",
            "--format=plain-vertical", f"--output-file={collected_file}",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    collected = collected_file.read_text(encoding="utf-8")
    collected_file.unlink()

    header = (
        "Full licence texts of the components bundled with Loci, as published by each\n"
        "package. PyMuPDF's licence is the GNU AGPL v3 (see LICENSE); Qt's is the GNU\n"
        "LGPL v3 (see LGPL-3.0.txt and GPL-3.0.txt); sqlite-vec's are in the\n"
        "sqlite-vec-LICENSE-*.txt files.\n\n"
    )
    (folder / "THIRD_PARTY_LICENSES.txt").write_text(header + collected, encoding="utf-8")

    (folder / "SOURCE.txt").write_text(
        f"{APP_NAME} {APP_VERSION} is free software under the GNU AGPL v3 (see LICENSE).\n"
        f"Its complete source code is at {REPOSITORY}\n"
        f"(tag v{APP_VERSION}: {REPOSITORY}/tree/v{APP_VERSION}).\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
