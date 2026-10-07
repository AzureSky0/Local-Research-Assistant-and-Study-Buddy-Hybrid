from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from sqlalchemy import func, select, text, update
from sqlalchemy.orm import Session

from app.documents.orm import DocumentORM
from app.knowledge.embeddings.embedding_models import EmbeddingModelSpec
from app.knowledge.orm.chunk_orm import ChunkORM
from app.knowledge.orm.vector_index_schema import (
    drop_vector_table,
    ensure_vector_table,
    existing_vector_tables,
    vector_table_name,
)


@dataclass(frozen=True, slots=True)
class PendingChunk:
    chunk_id: str
    workspace_id: str
    text: str


@dataclass(frozen=True, slots=True)
class VectorMatch:
    chunk_id: str
    distance: float  # cosine distance: 0 = same meaning


class VectorRepository:
    """Stores chunk vectors in sqlite-vec and finds the nearest ones.

    The repository never commits. Transaction boundaries belong to the
    service layer.
    """

    def __init__(self, session: Session, spec: EmbeddingModelSpec) -> None:
        self._session = session
        self._spec = spec
        self._table = vector_table_name(spec)

    def ensure_table(self) -> None:
        ensure_vector_table(self._session.connection(), self._spec)

    def drop_other_models(self) -> list[str]:
        """Remove vector tables of models no longer in use; returns their names."""
        connection = self._session.connection()
        dropped = [table for table in existing_vector_tables(connection) if table != self._table]

        for table in dropped:
            drop_vector_table(connection, table)

        if dropped:
            self._session.execute(
                update(ChunkORM)
                .where(ChunkORM.embedded_with.is_not(None), ChunkORM.embedded_with != self._spec.model_id)
                .values(embedded_with=None)
            )

        return dropped

    def pending_chunks(self, limit: int) -> list[PendingChunk]:
        """Chunks not yet embedded with this model, small documents first."""
        statement = (
            select(ChunkORM.id, DocumentORM.workspace_id, ChunkORM.text)
            .join(DocumentORM, DocumentORM.id == ChunkORM.document_id)
            .where(
                (ChunkORM.embedded_with.is_(None))
                | (ChunkORM.embedded_with != self._spec.model_id)
            )
            .order_by(DocumentORM.file_size, ChunkORM.document_id, ChunkORM.chunk_index)
            .limit(limit)
        )
        return [PendingChunk(row[0], row[1], row[2]) for row in self._session.execute(statement)]

    def add(self, chunks: Sequence[PendingChunk], vectors: np.ndarray) -> None:
        """Store vectors and mark their chunks as embedded with this model."""
        rows = [
            {
                "chunk_id": chunk.chunk_id,
                "workspace_id": chunk.workspace_id,
                "embedding": vector.astype(np.float32).tobytes(),
            }
            for chunk, vector in zip(chunks, vectors)
        ]

        # Replacing keeps this safe if a chunk was embedded before an interruption.
        self._session.execute(
            text(f"DELETE FROM {self._table} WHERE chunk_id = :chunk_id"),
            [{"chunk_id": row["chunk_id"]} for row in rows],
        )
        self._session.execute(
            text(
                f"INSERT INTO {self._table} (chunk_id, workspace_id, embedding) "
                "VALUES (:chunk_id, :workspace_id, :embedding)"
            ),
            rows,
        )
        self._session.execute(
            update(ChunkORM)
            .where(ChunkORM.id.in_([chunk.chunk_id for chunk in chunks]))
            .values(embedded_with=self._spec.model_id)
        )

    def nearest(self, workspace_id: str, query: np.ndarray, k: int) -> list[VectorMatch]:
        """The k chunks of a workspace closest in meaning to the query."""
        rows = self._session.execute(
            text(
                f"SELECT chunk_id, distance FROM {self._table} "
                "WHERE embedding MATCH :query AND k = :k AND workspace_id = :workspace_id "
                "ORDER BY distance"
            ),
            {"query": query.astype(np.float32).tobytes(), "k": k, "workspace_id": workspace_id},
        )
        return [VectorMatch(row[0], float(row[1])) for row in rows]

    def progress(self, workspace_id: str | None = None) -> tuple[int, int]:
        """(chunks embedded with this model, all chunks), optionally for one workspace."""
        embedded = func.sum(
            func.iif(ChunkORM.embedded_with == self._spec.model_id, 1, 0)
        )
        statement = select(embedded, func.count(ChunkORM.id))

        if workspace_id is not None:
            statement = statement.join(DocumentORM, DocumentORM.id == ChunkORM.document_id).where(
                DocumentORM.workspace_id == workspace_id
            )

        done, total = self._session.execute(statement).one()
        return int(done or 0), int(total or 0)
