import os
import sqlite3
from pathlib import Path

from app.database.backup import backup_database, remove_old_backups


def make_database(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("CREATE TABLE notes (text TEXT)")
    connection.execute("INSERT INTO notes VALUES ('kept')")
    connection.commit()
    connection.close()


def test_backup_is_a_full_copy(tmp_path: Path) -> None:
    database = tmp_path / "library.db"
    make_database(database)

    copy = backup_database(database, tmp_path / "backups", label="abc123")

    assert copy.name.startswith("library-before-abc123-")
    rows = sqlite3.connect(copy).execute("SELECT text FROM notes").fetchall()
    assert rows == [("kept",)]


def test_only_the_newest_backups_are_kept(tmp_path: Path) -> None:
    backups = tmp_path / "backups"
    backups.mkdir()
    for index in range(5):
        old = backups / f"library-before-rev{index}.db"
        old.write_bytes(b"")
        os.utime(old, (1000 + index, 1000 + index))

    remove_old_backups(backups, "library", keep=3)

    assert sorted(path.name for path in backups.iterdir()) == [
        "library-before-rev2.db",
        "library-before-rev3.db",
        "library-before-rev4.db",
    ]
