from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.tasks.task_status import TaskStatus


@dataclass(slots=True)
class TaskResult:
    """Represents the outcome of a background task."""

    status: TaskStatus
    value: Any = None
    error: Exception | None = None