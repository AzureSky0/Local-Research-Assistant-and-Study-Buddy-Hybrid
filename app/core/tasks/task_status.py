from enum import StrEnum


class TaskStatus(StrEnum):
    """Represents the lifecycle state of a background task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"