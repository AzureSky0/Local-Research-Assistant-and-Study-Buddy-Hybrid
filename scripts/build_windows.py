"""Build the Windows app for testers: dist/Loci/Loci.exe and a zip to share.

Usage (from the project root, inside the virtual environment):

    pip install pyinstaller
    python scripts/build_windows.py

Testers unzip the folder and double-click Loci.exe; no Python needed.
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


def main() -> None:
    subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", str(SPEC)],
        cwd=ROOT,
        check=True,
    )

    app_folder = DIST / APP_NAME
    archive = shutil.make_archive(
        str(DIST / f"{APP_NAME}-{APP_VERSION}-windows"), "zip", DIST, APP_NAME
    )

    size_mb = sum(f.stat().st_size for f in app_folder.rglob("*") if f.is_file()) / 1e6
    print(f"\nApp folder: {app_folder} ({size_mb:.0f} MB)")
    print(f"Zip to share: {archive} ({Path(archive).stat().st_size / 1e6:.0f} MB)")


if __name__ == "__main__":
    main()
