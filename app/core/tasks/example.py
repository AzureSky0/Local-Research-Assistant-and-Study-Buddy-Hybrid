from __future__ import annotations

from app.core.tasks.task import Task
from app.core.tasks.task_cancellation import TaskCancellationToken


class ExampleTask(Task):
    """Example task used for testing the task infrastructure."""

    @property
    def name(self) -> str:
        return "Example Task"

    def execute(
        self,
        cancellation_token: TaskCancellationToken,
        progress_callback,
    ) -> str:
        return "Task completed"