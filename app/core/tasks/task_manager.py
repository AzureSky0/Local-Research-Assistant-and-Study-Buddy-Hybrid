from __future__ import annotations

from uuid import UUID, uuid4

from app.core.tasks.task_handle import TaskHandle
from app.core.tasks.task_status import TaskStatus


class TaskManager:
    """Tracks submitted application tasks."""

    def __init__(self) -> None:
        self._tasks: dict[UUID, TaskHandle] = {}

    def register(self, handle: TaskHandle) -> UUID:
        """Register a task handle and return its task ID."""
        task_id = uuid4()
        self._tasks[task_id] = handle
        return task_id

    def get(self, task_id: UUID) -> TaskHandle | None:
        """Return a task handle by ID."""
        return self._tasks.get(task_id)

    def list_tasks(self) -> dict[UUID, TaskHandle]:
        """Return all registered tasks."""
        return self._tasks.copy()

    def remove(self, task_id: UUID) -> bool:
        """Remove a task and return whether it existed."""
        if task_id not in self._tasks:
            return False

        del self._tasks[task_id]
        return True

    def cleanup_completed(self) -> int:
        """Remove completed, failed, and cancelled tasks."""
        removable_statuses = {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        }

        task_ids_to_remove = [
            task_id
            for task_id, handle in self._tasks.items()
            if handle.status in removable_statuses
        ]

        for task_id in task_ids_to_remove:
            del self._tasks[task_id]

        return len(task_ids_to_remove)