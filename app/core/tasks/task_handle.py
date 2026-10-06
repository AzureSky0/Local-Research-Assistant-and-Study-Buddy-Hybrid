from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import Future
from threading import Lock

from app.core.tasks.task_cancellation import TaskCancellationToken
from app.core.tasks.task_progress import TaskProgress
from app.core.tasks.task_result import TaskResult
from app.core.tasks.task_status import TaskStatus


class TaskHandle:
    """Represents a submitted background task."""

    def __init__(
        self,
        cancellation_token: TaskCancellationToken,
        future: Future[TaskResult] | None = None,
    ) -> None:
        self._cancellation_token = cancellation_token
        self._future = future
        self._progress: TaskProgress | None = None
        self._progress_lock = Lock()
        self._status = TaskStatus.PENDING
        self._status_lock = Lock()

    def cancel(self) -> None:
        """Request cancellation of the task."""
        self._cancellation_token.cancel()

    @property
    def is_cancelled(self) -> bool:
        """Return whether cancellation has been requested."""
        return self._cancellation_token.is_cancelled

    @property
    def status(self) -> TaskStatus:
        """Return the current lifecycle status of the task."""
        with self._status_lock:
            return self._status

    def update_status(self, status: TaskStatus) -> None:
        """Update the lifecycle status of the task."""
        with self._status_lock:
            self._status = status

    @property
    def progress(self) -> TaskProgress | None:
        """Return the latest reported progress."""
        with self._progress_lock:
            return self._progress

    def update_progress(self, progress: TaskProgress) -> None:
        """Store the latest reported progress."""
        with self._progress_lock:
            self._progress = progress

    def set_future(self, future: Future[TaskResult]) -> None:
        """Associate the handle with its executor future."""
        self._future = future

    def result(self, timeout: float | None = None) -> TaskResult:
        """Wait for and return the task result."""
        if self._future is None:
            raise RuntimeError(
                "Task handle is not associated with a future."
            )

        return self._future.result(timeout=timeout)

    def add_done_callback(
        self,
        callback: Callable[[TaskResult], None],
    ) -> None:
        """Call `callback` with the task result once the task finishes.

        The callback runs on the worker thread that finished the task,
        or immediately on the calling thread if the task is already done.
        """
        if self._future is None:
            raise RuntimeError(
                "Task handle is not associated with a future."
            )

        self._future.add_done_callback(
            lambda future: callback(future.result())
        )

    @property
    def done(self) -> bool:
        """Return whether the task has finished."""
        if self._future is None:
            return False

        return self._future.done()