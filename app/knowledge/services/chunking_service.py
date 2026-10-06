from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy.orm import Session

from app.knowledge.repository.chunk_repository import ChunkRepository
from app.knowledge.services.text_chunker import CHUNKER_VERSION, chunk_pages


class ChunkingService:
    """Turns a document's pages into stored chunks (FR-KN-003).

    Owned by the Knowledge subsystem; the document processing pipeline
    hands it the pages. Runs inside the caller's transaction.
    """

    def __init__(self, session: Session) -> None:
        self._chunks = ChunkRepository(session)

    def chunk_document(self, document_id: str, pages: Iterable[tuple[int, str]]) -> int:
        """Rebuild a document's chunks from its pages. Returns the chunk count."""
        return self._chunks.replace_for_document(
            document_id,
            chunk_pages(pages),
            CHUNKER_VERSION,
        )
