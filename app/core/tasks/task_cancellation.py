from __future__ import annotations

from threading import Event


class TaskCancellationToken:
    """Provides cooperative cancellation for a background task."""

    def __init__(self) -> None:
        self._event = Event()

    def cancel(self) -> None:
        """Request cancellation of the task."""
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        """Return whether cancellation has been requested."""
        return self._event.is_set()

    def throw_if_cancelled(self) -> None:
        """Raise if cancellation has been requested."""
        if self.is_cancelled:
            raise TaskCancelledError


class TaskCancelledError(Exception):
    """Raised when a task detects a cancellation request."""