from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject, Signal
from sqlalchemy.orm import Session

from app.core.tasks.async_task_executor import AsyncTaskExecutor
from app.core.tasks.task_handle import TaskHandle
from app.core.tasks.task_result import TaskResult
from app.database.session import create_session
from app.documents.domain import Document
from app.documents.processing.document_processing_service import DocumentProcessingService
from app.documents.tasks.process_documents_task import ProcessDocumentsTask

SessionFactory = Callable[[], Session]


class ProcessingManager(QObject):
    """Reads imported documents in the background, one at a time.

    Runs on its own worker so reading never waits for imports and
    imports never wait for reading.
    """

    document_updated = Signal(object)  # Document

    # Emitted from the worker thread; delivered on the UI thread.
    _document_changed = Signal(object)  # Document
    _run_finished = Signal(object)  # TaskResult

    def __init__(
        self,
        executor: AsyncTaskExecutor,
        session_factory: SessionFactory = create_session,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._executor = executor
        self._session_factory = session_factory
        self._handle: TaskHandle | None = None
        self._more_work = False
        self._stopping = False

        self._document_changed.connect(self.document_updated)
        self._run_finished.connect(self._on_run_finished)

    @property
    def is_running(self) -> bool:
        return self._handle is not None

    def recover_and_start(self) -> None:
        """At start-up: requeue interrupted documents, then start reading."""
        with self._session_factory() as session:
            DocumentProcessingService(session).recover()

        self.start()

    def start(self) -> None:
        """Make sure pending documents are being read."""
        if self._stopping:
            return

        if self._handle is not None:
            # The running task reads new documents as well; this flag only
            # covers documents added just as it was finishing.
            self._more_work = True
            return

        task = ProcessDocumentsTask(
            session_factory=self._session_factory,
            on_document_started=self._document_changed.emit,
            on_document_finished=self._document_changed.emit,
        )

        self._handle = self._executor.submit(task)
        self._handle.add_done_callback(self._run_finished.emit)

    def retry(self, document_id: str) -> Document | None:
        """Read a failed document again."""
        with self._session_factory() as session:
            document = DocumentProcessingService(session).retry(document_id)

        if document is not None:
            self.document_updated.emit(document)
            self.start()

        return document

    def shutdown(self) -> None:
        """Stop after the current page and wait for the worker to exit."""
        self._stopping = True

        if self._handle is not None:
            self._handle.cancel()

        self._executor.shutdown()

    def _on_run_finished(self, result: TaskResult) -> None:
        self._handle = None

        if self._stopping:
            return

        if self._more_work or self._has_pending():
            self._more_work = False
            self.start()

    def _has_pending(self) -> bool:
        with self._session_factory() as session:
            return DocumentProcessingService(session).pending_count() > 0
