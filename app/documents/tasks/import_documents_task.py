from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.tasks.task import Task, TaskProgressCallback
from app.core.tasks.task_cancellation import TaskCancellationToken
from app.core.tasks.task_progress import TaskProgress
from app.database.session import create_session
from app.documents.dto.document_import_result import (
    DocumentImportResult,
    DocumentImportStatus,
)
from app.documents.services.document_import_service import (
    DocumentImportService,
    smallest_first,
)
from app.documents.services.document_service import DocumentService

SessionFactory = Callable[[], Session]

# Called on the worker thread after each file is handled.
ImportResultCallback = Callable[[DocumentImportResult], None]


@dataclass(slots=True)
class ImportBatchResult:
    """Outcome of one import operation (a set of files or a folder)."""

    results: list[DocumentImportResult]
    cancelled: bool

    def count(self, status: DocumentImportStatus) -> int:
        """Return how many files ended with the given status."""
        return sum(1 for result in self.results if result.status is status)


class ImportDocumentsTask(Task):
    """Imports files or a folder into a workspace in the background.

    The task opens its own database session because SQLAlchemy
    sessions must not be shared between threads.
    """

    def __init__(
        self,
        workspace_id: str,
        files: Sequence[Path] = (),
        folder: Path | None = None,
        session_factory: SessionFactory = create_session,
        on_result: ImportResultCallback | None = None,
    ) -> None:
        if folder is None and not files:
            raise ValueError("Provide files or a folder to import.")

        self._workspace_id = workspace_id
        self._files = list(files)
        self._folder = folder
        self._session_factory = session_factory
        self._on_result = on_result

    @property
    def name(self) -> str:
        if self._folder is not None:
            return f"Adding folder “{self._folder.name}”"

        if len(self._files) == 1:
            return f"Adding “{self._files[0].name}”"

        return f"Adding {len(self._files)} files"

    def execute(
        self,
        cancellation_token: TaskCancellationToken,
        progress_callback: TaskProgressCallback,
    ) -> ImportBatchResult:
        def on_progress(done: int, total: int, result: DocumentImportResult) -> None:
            if self._on_result is not None:
                self._on_result(result)

            progress_callback(
                TaskProgress(done, total, Path(result.file_path).name)
            )

        def is_cancelled() -> bool:
            return cancellation_token.is_cancelled

        with self._session_factory() as session:
            service = DocumentImportService(DocumentService(session))

            if self._folder is not None:
                progress_callback(TaskProgress(0, 0, "Looking for documents…"))

                results = service.import_folder(
                    self._workspace_id,
                    self._folder,
                    on_progress=on_progress,
                    is_cancelled=is_cancelled,
                )
            else:
                results = service.import_documents(
                    self._workspace_id,
                    smallest_first(self._files),
                    on_progress=on_progress,
                    is_cancelled=is_cancelled,
                )

        return ImportBatchResult(
            results=results,
            cancelled=cancellation_token.is_cancelled,
        )
