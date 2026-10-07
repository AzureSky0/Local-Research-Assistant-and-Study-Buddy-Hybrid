from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from PySide6.QtCore import QObject, QTimer, Signal
from sqlalchemy.orm import Session

from app.core.rate_estimator import RateEstimator
from app.core.system_monitor import (
    RECOVERED_MEMORY_MB,
    Health,
    SystemMonitor,
    SystemSnapshot,
    classify,
)
from app.database.session import create_session
from app.documents.processing.document_processing_service import DocumentProcessingService
from app.ui.managers.activity_manager import ActivityManager
from app.ui.managers.embedding_manager import EmbeddingManager
from app.ui.managers.processing_manager import ProcessingManager

logger = logging.getLogger(__name__)

SessionFactory = Callable[[], Session]

REFRESH_MILLISECONDS = 2000


class PauseReason(StrEnum):
    NONE = "none"
    USER = "user"
    LOW_MEMORY = "low_memory"


@dataclass(frozen=True, slots=True)
class BackgroundStatus:
    """Everything the status pill shows."""

    snapshot: SystemSnapshot | None
    health: Health
    pause_reason: PauseReason
    imports_running: int
    documents_to_read: int
    meaning_done: int
    meaning_total: int
    meaning_unavailable: bool
    # Estimates; None until there is enough progress to judge the pace.
    imports_seconds_left: float | None = None
    reading_seconds_left: float | None = None
    meaning_seconds_left: float | None = None

    @property
    def is_idle(self) -> bool:
        return (
            self.imports_running == 0
            and self.documents_to_read == 0
            and (self.meaning_unavailable or self.meaning_done >= self.meaning_total)
        )


class BackgroundManager(QObject):
    """Watches the computer and the app's background work (Decision 033).

    Publishes a status for the status pill every few seconds, lets the
    user pause all background work, and pauses it automatically when
    the computer runs low on memory (resuming once memory recovers).
    """

    status_changed = Signal(object)  # BackgroundStatus

    def __init__(
        self,
        activity: ActivityManager,
        processing: ProcessingManager,
        embedding: EmbeddingManager,
        monitor: SystemMonitor | None = None,
        session_factory: SessionFactory = create_session,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._activity = activity
        self._processing = processing
        self._embedding = embedding
        self._monitor = monitor or SystemMonitor()
        self._session_factory = session_factory

        self._user_paused = False
        self._memory_paused = False
        self._status: BackgroundStatus | None = None

        self._reading_pace = RateEstimator()
        self._documents_read = 0
        self._last_documents_to_read: int | None = None
        self._meaning_pace = RateEstimator()

        self._timer = QTimer(self)
        self._timer.setInterval(REFRESH_MILLISECONDS)
        self._timer.timeout.connect(self.refresh)

    def start(self) -> None:
        self._timer.start()
        self.refresh()

    def stop(self) -> None:
        self._timer.stop()

    @property
    def status(self) -> BackgroundStatus | None:
        return self._status

    @property
    def pause_reason(self) -> PauseReason:
        if self._user_paused:
            return PauseReason.USER
        if self._memory_paused:
            return PauseReason.LOW_MEMORY
        return PauseReason.NONE

    # Commands ----------------------------------------------------------------------

    def pause(self) -> None:
        """Pause all background work until the user resumes it."""
        self._user_paused = True
        self._apply_pause()
        self.refresh()

    def resume(self) -> None:
        self._user_paused = False
        self._apply_pause()
        self.refresh()

    # Internals ----------------------------------------------------------------------

    def refresh(self, snapshot: SystemSnapshot | None = None) -> None:
        snapshot = snapshot or self._monitor.snapshot()
        health = classify(snapshot)

        # Automatic protection, with a margin so it does not flicker.
        if health is Health.LOW_MEMORY and not self._memory_paused:
            logger.warning("Low memory (%.0f MB free): pausing background work", snapshot.memory_available_mb)
            self._memory_paused = True
            self._apply_pause()
        elif self._memory_paused and snapshot.memory_available_mb >= RECOVERED_MEMORY_MB:
            logger.info("Memory recovered: resuming background work")
            self._memory_paused = False
            self._apply_pause()

        meaning_done, meaning_total = self._embedding.progress()
        documents_to_read = self._documents_to_read()
        imports_seconds_left, reading_seconds_left, meaning_seconds_left = self._estimate(
            documents_to_read, meaning_done, meaning_total
        )

        self._status = BackgroundStatus(
            snapshot=snapshot,
            health=health,
            pause_reason=self.pause_reason,
            imports_running=self._activity.running_count,
            documents_to_read=documents_to_read,
            meaning_done=meaning_done,
            meaning_total=meaning_total,
            meaning_unavailable=self._embedding.unavailable_message is not None,
            imports_seconds_left=imports_seconds_left,
            reading_seconds_left=reading_seconds_left,
            meaning_seconds_left=meaning_seconds_left,
        )
        self.status_changed.emit(self._status)

    def _estimate(
        self, documents_to_read: int, meaning_done: int, meaning_total: int
    ) -> tuple[float | None, float | None, float | None]:
        imports = [a.seconds_left for a in self._activity.activities if a.is_running]
        imports_seconds_left = max((s for s in imports if s is not None), default=None)

        # New imports add documents to read, so count the finished ones.
        if self._last_documents_to_read is not None:
            self._documents_read += max(0, self._last_documents_to_read - documents_to_read)
        self._last_documents_to_read = documents_to_read

        if self.pause_reason is not PauseReason.NONE:
            return imports_seconds_left, None, None

        # Idle time would make the next batch look slower than it is.
        for pace, finished, remaining in (
            (self._reading_pace, self._documents_read, documents_to_read),
            (self._meaning_pace, meaning_done, meaning_total - meaning_done),
        ):
            if remaining > 0:
                pace.record(finished)
            else:
                pace.reset()

        return (
            imports_seconds_left,
            self._reading_pace.seconds_left(documents_to_read),
            self._meaning_pace.seconds_left(meaning_total - meaning_done),
        )

    def _apply_pause(self) -> None:
        # Time spent paused says nothing about the pace.
        self._reading_pace.reset()
        self._meaning_pace.reset()

        if self.pause_reason is PauseReason.NONE:
            self._processing.resume()
            self._embedding.resume()
        else:
            self._processing.pause()
            self._embedding.pause()

    def _documents_to_read(self) -> int:
        with self._session_factory() as session:
            return DocumentProcessingService(session).pending_count() + (
                1 if self._processing.is_running and not self._processing.is_paused else 0
            )
