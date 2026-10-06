from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable

from app.core.tasks.task_cancellation import TaskCancellationToken

from app.core.tasks.task_progress import TaskProgress

TaskProgressCallback = Callable[[TaskProgress], None]


class Task(ABC):
    """Base abstraction for an executable background task."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the human-readable task name."""
        raise NotImplementedError

    @abstractmethod
    def execute(
        self,
        cancellation_token: TaskCancellationToken,
        progress_callback: TaskProgressCallback,
    ) -> Any:
        """Execute the task and return its result."""
        raise NotImplementedError