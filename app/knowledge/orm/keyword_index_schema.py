"""SQLite FTS5 keyword index over document pages (owned by Knowledge).

FTS5 virtual tables and triggers cannot be described as ORM models,
so the schema is plain DDL. It is created by an Alembic migration in
the application and attached to Base.metadata so `create_all` (used by
tests) creates it too.

Keep these statements in sync with migration c3e8a1f45d27.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import event, text

from app.database.base import Base

KEYWORD_INDEX_TABLE = "page_search"

# porter: "learn" also finds "learning"; remove_diacritics: "cafe" finds "café".
KEYWORD_INDEX_DDL = [
    f"""
    CREATE VIRTUAL TABLE IF NOT EXISTS {KEYWORD_INDEX_TABLE} USING fts5(
        text,
        document_id UNINDEXED,
        page_number UNINDEXED,
        tokenize = 'porter unicode61 remove_diacritics 2'
    )
    """,
    # Removing a document (or its workspace, by cascade) removes it
    # from the index as well.
    f"""
    CREATE TRIGGER IF NOT EXISTS documents_delete_from_{KEYWORD_INDEX_TABLE}
    AFTER DELETE ON documents
    BEGIN
        DELETE FROM {KEYWORD_INDEX_TABLE} WHERE document_id = old.id;
    END
    """,
]


def is_keyword_index_table(name: str | None) -> bool:
    """True for the FTS5 table and its shadow tables (ignored by Alembic)."""
    return bool(name) and str(name).startswith(KEYWORD_INDEX_TABLE)


@event.listens_for(Base.metadata, "after_create")
def _create_keyword_index(target: Any, connection: Any, **kwargs: Any) -> None:
    for statement in KEYWORD_INDEX_DDL:
        connection.execute(text(statement))
