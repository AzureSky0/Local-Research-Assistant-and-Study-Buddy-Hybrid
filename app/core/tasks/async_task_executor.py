from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

from app.core.tasks.task import Task, TaskProgressCallback
from app.core.tasks.task_cancellation import (
    TaskCancellationToken,
    TaskCancelledError,
)
from app.core.tasks.task_handle import TaskHandle
from app.core.tasks.task_progress import TaskProgress
from app.core.tasks.task_result import TaskResult
from app.core.tasks.task_status import TaskStatus

logger = logging.getLogger(__name__)


class AsyncTaskExecutor:
    """Executes tasks in a background thread pool."""

    def __init__(
        self,
        max_workers: int = 4,
    ) -> None:
        if max_workers < 1:
            raise ValueError("max_workers must be at least 1")

        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
        )

    def submit(
        self,
        task: Task,
        progress_callback: TaskProgressCallback | None = None,
    ) -> TaskHandle:
        """Submit a task for background execution."""

        cancellation_token = TaskCancellationToken()

        handle = TaskHandle(
            cancellation_token=cancellation_token,
        )

        if progress_callback is None:
            progress_callback = handle.update_progress
        else:
            original_callback = progress_callback

            def report_progress(progress: TaskProgress) -> None:
                handle.update_progress(progress)
                original_callback(progress)

            progress_callback = report_progress

        future = self._executor.submit(
            self._execute_task,
            task,
            cancellation_token,
            progress_callback,
            handle,
        )

        handle.set_future(future)

        return handle

    @staticmethod
    def _execute_task(
        task: Task,
        cancellation_token: TaskCancellationToken,
        progress_callback: TaskProgressCallback,
        handle: TaskHandle,
    ) -> TaskResult:
        """Execute the task inside a worker thread."""

        if cancellation_token.is_cancelled:
            handle.update_status(TaskStatus.CANCELLED)

            return TaskResult(
                status=TaskStatus.CANCELLED,
            )

        handle.update_status(TaskStatus.RUNNING)

        try:
            result = task.execute(
                cancellation_token,
                progress_callback,
            )

        except TaskCancelledError:
            handle.update_status(TaskStatus.CANCELLED)

            return TaskResult(
                status=TaskStatus.CANCELLED,
            )

        except Exception as error:
            logger.exception("Task failed: %s", task.name)

            handle.update_status(TaskStatus.FAILED)

            return TaskResult(
                status=TaskStatus.FAILED,
                error=error,
            )

        handle.update_status(TaskStatus.COMPLETED)

        return TaskResult(
            status=TaskStatus.COMPLETED,
            value=result,
        )

    def shutdown(self) -> None:
        """Shut down the underlying thread pool."""

        self._executor.shutdown(
            wait=True,
        )