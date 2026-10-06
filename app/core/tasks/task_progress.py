from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TaskProgress:
    """Represents the progress of a background task."""

    current: int
    total: int
    message: str = ""

    def __post_init__(self) -> None:
        if self.total < 0:
            raise ValueError("total cannot be negative")

        if self.current < 0:
            raise ValueError("current cannot be negative")

        if self.current > self.total:
            raise ValueError(
                "current cannot be greater than total"
            )

    @property
    def percentage(self) -> int:
        """Return progress as a percentage."""

        if self.total == 0:
            return 0

        return int(
            (self.current / self.total) * 100
        )