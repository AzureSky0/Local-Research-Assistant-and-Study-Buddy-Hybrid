from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.knowledge.orm.chunk_orm import ChunkORM
from app.knowledge.services.text_chunker import Chunk


class ChunkRepository:
    """Persistence for document chunks.

    The repository never commits. Transaction boundaries belong
    to the service layer.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def replace_for_document(
        self,
        document_id: str,
        chunks: Iterable[Chunk],
        chunker_version: str,
    ) -> int:
        """Replace a document's chunks. Returns how many were stored."""
        self.delete_for_document(document_id)

        count = 0
        for chunk in chunks:
            self._session.add(
                ChunkORM(
                    document_id=document_id,
                    chunk_index=chunk.index,
                    text=chunk.text,
                    start_page=chunk.start_page,
                    end_page=chunk.end_page,
                    word_count=chunk.word_count,
                    chunker_version=chunker_version,
                )
            )
            count += 1

        self._session.flush()
        return count

    def delete_for_document(self, document_id: str) -> None:
        self._session.execute(delete(ChunkORM).where(ChunkORM.document_id == document_id))

    def list_for_document(self, document_id: str) -> list[ChunkORM]:
        statement = (
            select(ChunkORM)
            .where(ChunkORM.document_id == document_id)
            .order_by(ChunkORM.chunk_index)
        )
        return list(self._session.scalars(statement))

    def count_for_document(self, document_id: str) -> int:
        statement = select(func.count(ChunkORM.id)).where(ChunkORM.document_id == document_id)
        return int(self._session.scalar(statement) or 0)
