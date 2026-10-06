from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from uuid import UUID, uuid4

from PySide6.QtCore import QObject, Signal
from sqlalchemy.orm import Session

from app.core.tasks.async_task_executor import AsyncTaskExecutor
from app.core.tasks.task_handle import TaskHandle
from app.core.tasks.task_progress import TaskProgress
from app.core.tasks.task_result import TaskResult
from app.core.tasks.task_status import TaskStatus
from app.database.session import create_session
from app.documents.dto.document_import_result import (
    DocumentImportResult,
    DocumentImportStatus,
)
from app.documents.tasks.import_documents_task import (
    ImportBatchResult,
    ImportDocumentsTask,
)

SessionFactory = Callable[[], Session]


class ActivityState(StrEnum):
    RUNNING = "running"
    FINISHED = "finished"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass(slots=True)
class ImportActivity:
    """UI-facing state of one import. Only changed on the UI thread."""

    id: UUID
    workspace_id: str
    workspace_name: str
    title: str
    started_at: float
    state: ActivityState = ActivityState.RUNNING
    done: int = 0
    total: int = 0
    current_item: str = ""
    finished_at: float | None = None
    error: str | None = None
    results: list[DocumentImportResult] = field(default_factory=list)

    def count(self, status: DocumentImportStatus) -> int:
        return sum(1 for result in self.results if result.status is status)

    @property
    def is_running(self) -> bool:
        return self.state is ActivityState.RUNNING

    @property
    def seconds_left(self) -> float | None:
        """Estimate remaining time from the average time per file so far."""
        if self.done < 3 or self.total <= self.done:
            return None

        elapsed = time.monotonic() - self.started_at
        return elapsed / self.done * (self.total - self.done)


class ActivityManager(QObject):
    """Runs imports in the background and reports their progress to the UI."""

    activity_started = Signal(object)  # ImportActivity
    activity_updated = Signal(object)  # ImportActivity
    activity_finished = Signal(object)  # ImportActivity
    document_imported = Signal(object)  # Document
    running_count_changed = Signal(int)

    # Emitted from worker threads; delivered on the UI thread.
    _progress_reported = Signal(object, object)  # UUID, TaskProgress
    _result_reported = Signal(object, object)  # UUID, DocumentImportResult
    _task_completed = Signal(object, object)  # UUID, TaskResult

    def __init__(
        self,
        executor: AsyncTaskExecutor,
        session_factory: SessionFactory = create_session,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._executor = executor
        self._session_factory = session_factory
        self._handles: dict[UUID, TaskHandle] = {}
        self._activities: dict[UUID, ImportActivity] = {}

        self._progress_reported.connect(self._on_progress)
        self._result_reported.connect(self._on_result)
        self._task_completed.connect(self._on_completed)

    # Public API ------------------------------------------------------------

    @property
    def activities(self) -> list[ImportActivity]:
        """All activities, newest first."""
        return sorted(
            self._activities.values(),
            key=lambda activity: activity.started_at,
            reverse=True,
        )

    @property
    def running_count(self) -> int:
        return sum(1 for activity in self._activities.values() if activity.is_running)

    def import_files(
        self,
        workspace_id: str,
        workspace_name: str,
        files: Sequence[Path],
    ) -> ImportActivity:
        return self._start(workspace_id, workspace_name, files=files)

    def import_folder(
        self,
        workspace_id: str,
        workspace_name: str,
        folder: Path,
    ) -> ImportActivity:
        return self._start(workspace_id, workspace_name, folder=folder)

    def cancel(self, activity_id: UUID) -> None:
        """Stop an import before its next file. Imported files are kept."""
        handle = self._handles.get(activity_id)

        if handle is not None:
            handle.cancel()

    def cancel_all(self) -> None:
        for activity_id, activity in self._activities.items():
            if activity.is_running:
                self.cancel(activity_id)

    def clear_finished(self) -> None:
        for activity_id in [
            activity_id
            for activity_id, activity in self._activities.items()
            if not activity.is_running
        ]:
            del self._activities[activity_id]
            self._handles.pop(activity_id, None)

    def shutdown(self) -> None:
        """Cancel running imports and wait for worker threads to stop."""
        self.cancel_all()
        self._executor.shutdown()

    # Internals ---------------------------------------------------------------

    def _start(
        self,
        workspace_id: str,
        workspace_name: str,
        files: Sequence[Path] = (),
        folder: Path | None = None,
    ) -> ImportActivity:
        # Created before submitting: worker callbacks may fire immediately.
        activity_id = uuid4()

        task = ImportDocumentsTask(
            workspace_id,
            files=files,
            folder=folder,
            session_factory=self._session_factory,
            on_result=lambda result: self._result_reported.emit(activity_id, result),
        )

        handle = self._executor.submit(
            task,
            progress_callback=lambda progress: self._progress_reported.emit(
                activity_id, progress
            ),
        )
        self._handles[activity_id] = handle

        activity = ImportActivity(
            id=activity_id,
            workspace_id=workspace_id,
            workspace_name=workspace_name,
            title=task.name,
            started_at=time.monotonic(),
            total=len(files),
        )
        self._activities[activity_id] = activity

        self.activity_started.emit(activity)
        self.running_count_changed.emit(self.running_count)

        # Registered last: if the task has already finished, the callback
        # runs immediately and must find the activity already announced.
        handle.add_done_callback(
            lambda result: self._task_completed.emit(activity_id, result)
        )

        return activity

    def _on_progress(self, activity_id: UUID, progress: TaskProgress) -> None:
        activity = self._activities.get(activity_id)

        if activity is None or not activity.is_running:
            return

        activity.done = progress.current
        activity.total = progress.total
        activity.current_item = progress.message
        self.activity_updated.emit(activity)

    def _on_result(self, activity_id: UUID, result: DocumentImportResult) -> None:
        activity = self._activities.get(activity_id)

        if activity is None:
            return

        activity.results.append(result)

        if result.status is DocumentImportStatus.IMPORTED and result.document is not None:
            self.document_imported.emit(result.document)

    def _on_completed(self, activity_id: UUID, task_result: TaskResult) -> None:
        activity = self._activities.get(activity_id)

        if activity is None:
            return

        activity.finished_at = time.monotonic()
        activity.current_item = ""

        batch = task_result.value

        if task_result.status is TaskStatus.COMPLETED and isinstance(batch, ImportBatchResult):
            # The batch is authoritative: it also contains files that were
            # never imported (unsupported files, unreadable folders).
            activity.results = list(batch.results)
            activity.state = (
                ActivityState.CANCELLED if batch.cancelled else ActivityState.FINISHED
            )
        elif task_result.status is TaskStatus.CANCELLED:
            activity.state = ActivityState.CANCELLED
        else:
            activity.state = ActivityState.FAILED
            activity.error = str(task_result.error) if task_result.error else "Unknown error"

        self.activity_finished.emit(activity)
        self.running_count_changed.emit(self.running_count)
