from __future__ import annotations

from app.core.tasks.task import Task
from app.core.tasks.task_cancellation import (
    TaskCancellationToken,
    TaskCancelledError,
)
from app.core.tasks.task_progress import TaskProgress
from app.core.tasks.task_result import TaskResult
from app.core.tasks.task_status import TaskStatus


def _ignore_progress(progress: TaskProgress) -> None:
    """Ignore progress updates for synchronous execution."""


class TaskExecutor:
    """Executes tasks and returns their results."""

    def execute(self, task: Task) -> TaskResult:
        """Execute a task and capture its outcome."""

        try:
            result = task.execute(
                TaskCancellationToken(),
                _ignore_progress,
            )

        except TaskCancelledError:
            return TaskResult(
                status=TaskStatus.CANCELLED,
            )

        except Exception as error:
            return TaskResult(
                status=TaskStatus.FAILED,
                error=error,
            )

        return TaskResult(
            status=TaskStatus.COMPLETED,
            value=result,
        )