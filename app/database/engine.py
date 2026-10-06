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
    """

    @event.listens_for(engine, "connect")
    def _configure(dbapi_connection: Any, connection_record: Any) -> None:
        if isinstance(dbapi_connection, SQLiteConnection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()


engine = create_engine(
    DATABASE_URL,
    echo=False,
)

configure_sqlite_connections(engine)
