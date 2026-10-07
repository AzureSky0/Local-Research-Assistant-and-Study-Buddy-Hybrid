from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session

from app.core.tasks.task import Task, TaskProgressCallback
from app.core.tasks.task_cancellation import TaskCancellationToken
from app.core.tasks.task_progress import TaskProgress
from app.database.session import create_session
from app.knowledge.embeddings.embedder import Embedder
from app.knowledge.services.embedding_service import EmbeddingService

SessionFactory = Callable[[], Session]


class EmbedChunksTask(Task):
    """Embeds every pending chunk in the background, then stops.

    The task opens its own database session (sessions must not be
    shared between threads). Raises EmbeddingModelUnavailableError when
    the model cannot be loaded, for example offline before the first
    download.
    """

    def __init__(
        self,
        embedder: Embedder,
        session_factory: SessionFactory = create_session,
    ) -> None:
        self._embedder = embedder
        self._session_factory = session_factory

    @property
    def name(self) -> str:
        return "Preparing search by meaning"

    def execute(
        self,
        cancellation_token: TaskCancellationToken,
        progress_callback: TaskProgressCallback,
    ) -> int:
        with self._session_factory() as session:
            service = EmbeddingService(session, self._embedder)
            service.prepare()

            done, total = service.progress()
            progress_callback(TaskProgress(done, total, ""))

            if done >= total:
                return 0

            # Loading the model may download it the first time.
            self._embedder.load_model()

            return service.embed_pending(
                is_cancelled=lambda: cancellation_token.is_cancelled,
                on_progress=lambda done, total: progress_callback(
                    TaskProgress(min(done, total), total, "")
                ),
            )
