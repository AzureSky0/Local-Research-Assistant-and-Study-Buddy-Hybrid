from __future__ import annotations

import logging
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.database.transaction import commit
from app.knowledge.embeddings.embedder import Embedder
from app.knowledge.repository.vector_repository import VectorRepository

logger = logging.getLogger(__name__)

# Chunks embedded and committed together; small enough that an
# interruption loses little work and the database is never locked long.
EMBED_BATCH = 64

ProgressCallback = Callable[[int, int], None]  # (embedded, total)


class EmbeddingService:
    """Builds the vector index for search by meaning (Decision 035).

    Owned by the Knowledge subsystem. Works through every chunk that has
    not been embedded with the current model, in batches across documents,
    and commits after each batch so it can stop and resume at any time.
    Document status is not affected: documents are searchable by keyword
    before their vectors exist (Decision 031).
    """

    def __init__(self, session: Session, embedder: Embedder) -> None:
        self._session = session
        self._embedder = embedder
        self._vectors = VectorRepository(session, embedder.spec)

    def prepare(self) -> None:
        """Create this model's vector table and remove other models' tables."""
        self._vectors.ensure_table()
        dropped = self._vectors.drop_other_models()

        if dropped:
            logger.info("Removed vectors of previous models: %s", ", ".join(dropped))

        commit(self._session)

    def progress(self, workspace_id: str | None = None) -> tuple[int, int]:
        return self._vectors.progress(workspace_id)

    def embed_pending(
        self,
        is_cancelled: Callable[[], bool] = lambda: False,
        on_progress: ProgressCallback | None = None,
    ) -> int:
        """Embed all pending chunks; returns how many were embedded."""

        embedded = 0

        while not is_cancelled():
            batch = self._vectors.pending_chunks(EMBED_BATCH)

            if not batch:
                break

            vectors = self._embedder.embed_passages([chunk.text for chunk in batch])
            self._vectors.add(batch, vectors)
            commit(self._session)
            embedded += len(batch)

            if on_progress is not None:
                on_progress(*self._vectors.progress())

        return embedded
