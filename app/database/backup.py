"""Copy the library database before a new version changes its format.

A new version may migrate the database on its first start. If that ever
goes wrong, the copy made just before lets the library be restored.
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Older copies are removed so backups do not fill the disk.
BACKUPS_TO_KEEP = 3


def backup_database(database_path: Path, backup_dir: Path, label: str) -> Path:
    """Write a consistent copy of the database to backup_dir and return its path.

    Uses SQLite's backup API, so changes still in the WAL file are included.
    """
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = backup_dir / f"{database_path.stem}-before-{label}-{stamp}{database_path.suffix}"

    source = sqlite3.connect(database_path)
    try:
        destination = sqlite3.connect(target)
        try:
            source.backup(destination)
        finally:
            destination.close()
    finally:
        source.close()

    remove_old_backups(backup_dir, database_path.stem, BACKUPS_TO_KEEP)
    logger.info("Database backed up to %s", target)
    return target


def remove_old_backups(backup_dir: Path, stem: str, keep: int) -> None:
    backups = sorted(backup_dir.glob(f"{stem}-before-*"), key=lambda path: path.stat().st_mtime)
    for old in backups[:-keep]:
        old.unlink(missing_ok=True)
