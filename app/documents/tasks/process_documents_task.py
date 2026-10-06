from __future__ import annotations

from collections.abc import Callable, Sequence

from sqlalchemy.orm import Session

from app.core.tasks.task import Task, TaskProgressCallback
from app.core.tasks.task_cancellation import TaskCancellationToken
from app.core.tasks.task_progress import TaskProgress
from app.database.session import create_session
from app.documents.domain import Document
from app.documents.processing.document_processing_service import DocumentProcessingService
from app.documents.processing.processing_stage import (
    ProcessingCancelledError,
    ProcessingStage,
)

SessionFactory = Callable[[], Session]
DocumentCallback = Callable[[Document], None]


class ProcessDocumentsTask(Task):
    """Processes pending documents one at a time until none are left.

    Documents imported while the task runs are picked up too, because
    the queue is read from the database before each document.
    """

    def __init__(
        self,
        session_factory: SessionFactory = create_session,
        stages_factory: Callable[[], Sequence[ProcessingStage]] | None = None,
        on_document_started: DocumentCallback | None = None,
        on_document_finished: DocumentCallback | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._stages_factory = stages_factory
        self._on_started = on_document_started
        self._on_finished = on_document_finished

    @property
    def name(self) -> str:
        return "Reading documents"

    def execute(
        self,
        cancellation_token: TaskCancellationToken,
        progress_callback: TaskProgressCallback,
    ) -> int:
        """Return how many documents were processed."""

        processed = 0
        attempted: set[str] = set()

        def is_cancelled() -> bool:
            return cancellation_token.is_cancelled

        with self._session_factory() as session:
            stages = self._stages_factory() if self._stages_factory else None
            service = DocumentProcessingService(session, stages)

            while not cancellation_token.is_cancelled:
                # Each document is attempted once per run, so a document
                # that stays pending can never cause an endless loop.
                document_id = service.next_document_id(exclude=attempted)

                if document_id is None:
                    break

                attempted.add(document_id)
                remaining = service.pending_count() - 1

                progress_callback(
                    TaskProgress(processed, processed + 1 + max(remaining, 0), "")
                )

                try:
                    document = service.process(
                        document_id,
                        is_cancelled=is_cancelled,
                        on_started=self._on_started,
                    )
                except ProcessingCancelledError:
                    break

                processed += 1

                if document is not None and self._on_finished is not None:
                    self._on_finished(document)

        return processed
