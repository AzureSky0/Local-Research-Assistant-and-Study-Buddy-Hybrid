from sqlite3 import Connection as SQLiteConnection
from typing import Any

from sqlalchemy import Engine, create_engine, event

from app.core.constants import DATABASE_FILENAME
from app.core.paths import DATABASE_DIR

DATABASE_PATH = DATABASE_DIR / DATABASE_FILENAME

DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"


def configure_sqlite_connections(engine: Engine) -> None:
    """Apply SQLite settings to every new connection.

    - foreign_keys: SQLite ignores foreign keys (including
      ON DELETE CASCADE) unless enabled per connection.
    - journal_mode=WAL: lets the UI read while background tasks
      write. Has no effect on in-memory databases.
    - synchronous=NORMAL: safe with WAL and much faster for
      the many small writes made during document processing.
    - sqlite-vec: the vector index for search by meaning (Decision 035).
    """

    @event.listens_for(engine, "connect")
    def _configure(dbapi_connection: Any, connection_record: Any) -> None:
        if isinstance(dbapi_connection, SQLiteConnection):
            _load_sqlite_vec(dbapi_connection)

            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()


def _load_sqlite_vec(connection: SQLiteConnection) -> None:
    import sqlite_vec  # type: ignore[import-untyped]

    connection.enable_load_extension(True)
    try:
        sqlite_vec.load(connection)
    finally:
        connection.enable_load_extension(False)


# Imports and background reading write at the same time. With WAL only
# one write happens at once, so writers wait (up to this many seconds)
# instead of failing immediately with "database is locked".
BUSY_TIMEOUT_SECONDS = 30

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"timeout": BUSY_TIMEOUT_SECONDS},
)

configure_sqlite_connections(engine)
