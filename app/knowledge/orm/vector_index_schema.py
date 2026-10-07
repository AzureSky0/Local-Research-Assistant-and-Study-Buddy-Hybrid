"""sqlite-vec vector tables for search by meaning (Knowledge subsystem).

One table per embedding model, because each model has its own vector
size and vectors from different models cannot be compared. Tables are
created when a model is first used, partitioned by workspace so a search
only ever looks inside one workspace (PRD §90), and cleaned up by a
trigger when chunks are deleted (including by cascade).
"""

from __future__ import annotations

from sqlalchemy import Connection, text

from app.knowledge.embeddings.embedding_models import EmbeddingModelSpec

VECTOR_TABLE_PREFIX = "chunk_vectors_"


def vector_table_name(spec: EmbeddingModelSpec) -> str:
    return f"{VECTOR_TABLE_PREFIX}{spec.key}"


def is_vector_index_table(name: str | None) -> bool:
    """True for vector tables and their sqlite-vec shadow tables (ignored by Alembic)."""
    return bool(name) and str(name).startswith(VECTOR_TABLE_PREFIX)


def ensure_vector_table(connection: Connection, spec: EmbeddingModelSpec) -> str:
    """Create the vector table and its clean-up trigger for a model if missing."""

    table = vector_table_name(spec)

    connection.execute(
        text(
            f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS {table} USING vec0(
                chunk_id TEXT PRIMARY KEY,
                workspace_id TEXT PARTITION KEY,
                embedding FLOAT[{spec.dimension}] distance_metric=cosine
            )
            """
        )
    )

    connection.execute(
        text(
            f"""
            CREATE TRIGGER IF NOT EXISTS chunks_delete_from_{table}
            AFTER DELETE ON chunks
            BEGIN
                DELETE FROM {table} WHERE chunk_id = old.id;
            END
            """
        )
    )

    return table


def drop_vector_table(connection: Connection, table: str) -> None:
    connection.execute(text(f"DROP TRIGGER IF EXISTS chunks_delete_from_{table}"))
    connection.execute(text(f"DROP TABLE IF EXISTS {table}"))


def existing_vector_tables(connection: Connection) -> list[str]:
    rows = connection.execute(
        text(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND sql LIKE 'CREATE VIRTUAL TABLE%' AND name LIKE :prefix"
        ),
        {"prefix": f"{VECTOR_TABLE_PREFIX}%"},
    )
    return [row[0] for row in rows]
