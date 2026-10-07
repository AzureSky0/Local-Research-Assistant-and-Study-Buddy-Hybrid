# PyInstaller build for Windows testers: a "Loci" folder with Loci.exe.
# Build with:  python scripts/build_windows.py
# ruff: noqa

import re
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

ROOT = Path(SPECPATH).parent
APP_NAME = "Loci"

datas = [
    # Alembic reads the config and migration scripts from disk at start-up.
    (str(ROOT / "alembic.ini"), "."),
    (str(ROOT / "app" / "database" / "migrations"), "app/database/migrations"),
]
datas += collect_data_files("fastembed")

# The vector index is a SQLite extension loaded from the sqlite_vec package folder.
binaries = collect_dynamic_libs("sqlite_vec")


def migration_imports() -> list[str]:
    """Modules imported by the migration scripts.

    Alembic loads them from disk at start-up, so PyInstaller never sees
    their imports; without this a new migration could break the app.
    """
    modules = set()
    for script in (ROOT / "app" / "database" / "migrations").rglob("*.py"):
        for line in script.read_text(encoding="utf-8").splitlines():
            match = re.match(r"(?:from|import)\s+([\w.]+)", line)
            if match:
                modules.add(match.group(1))
    return sorted(modules)


# Some modules are imported lazily (migrations, fastembed models).
hiddenimports = (
    migration_imports()
    + collect_submodules("alembic")
    + collect_submodules("fastembed")
    + collect_submodules("app")
)

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["tkinter", "pytest", "mypy", "black", "ruff", "IPython", "matplotlib"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    console=False,  # a windowed app; logs go to the data folder
    upx=False,
)

coll = COLLECT(exe, a.binaries, a.datas, name=APP_NAME, upx=False)
