from collections.abc import Callable, Generator

import pytest
from PySide6.QtWidgets import QApplication
from sqlalchemy.orm import Session

from app.core.system_monitor import (
    LOW_MEMORY_MB,
    RECOVERED_MEMORY_MB,
    Health,
    SystemMonitor,
    SystemSnapshot,
    classify,
)
from app.core.tasks.async_task_executor import AsyncTaskExecutor
from app.core.user_preferences import UserPreferences
from app.ui.managers.activity_manager import ActivityManager
from app.ui.managers.background_manager import BackgroundManager, BackgroundStatus, PauseReason
from app.ui.managers.embedding_manager import EmbeddingManager
from app.ui.managers.processing_manager import ProcessingManager
from app.ui.widgets.status_pill import describe
from tests.knowledge.fake_embedder import FakeEmbedder


def snapshot(available_mb: float = 6000, cpu: float = 20) -> SystemSnapshot:
    return SystemSnapshot(
        app_memory_mb=300,
        app_cpu_percent=5,
        system_cpu_percent=cpu,
        memory_used_mb=16000 - available_mb,
        memory_total_mb=16000,
        memory_available_mb=available_mb,
    )


# Health ------------------------------------------------------------------------------------


def test_health_classification() -> None:
    assert classify(snapshot()) is Health.OK
    assert classify(snapshot(cpu=95)) is Health.BUSY
    assert classify(snapshot(available_mb=LOW_MEMORY_MB - 1, cpu=95)) is Health.LOW_MEMORY


def test_real_snapshot_is_sensible() -> None:
    monitor = SystemMonitor()
    reading = monitor.snapshot()

    assert reading.app_memory_mb > 0
    assert 0 < reading.memory_used_mb <= reading.memory_total_mb
    assert 0 <= reading.system_cpu_percent <= 100
    assert 0 <= reading.app_cpu_percent <= 100


# Pill wording -------------------------------------------------------------------------------


def status(**changes: object) -> BackgroundStatus:
    values: dict[str, object] = {
        "snapshot": snapshot(),
        "health": Health.OK,
        "pause_reason": PauseReason.NONE,
        "imports_running": 0,
        "documents_to_read": 0,
        "meaning_done": 10,
        "meaning_total": 10,
        "meaning_unavailable": False,
    }
    values.update(changes)
    return BackgroundStatus(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({}, "All caught up"),
        ({"documents_to_read": 3}, "Reading 3 documents"),
        ({"meaning_done": 45, "meaning_total": 100}, "Preparing search by meaning"),
        (
            {"imports_running": 1, "documents_to_read": 1, "meaning_done": 1, "meaning_total": 4},
            "Adding files · Reading 1 document · Preparing search by meaning",
        ),
        ({"meaning_done": 1, "meaning_total": 4, "meaning_unavailable": True}, "All caught up"),
        ({"pause_reason": PauseReason.USER, "documents_to_read": 3}, "Background work paused"),
        ({"pause_reason": PauseReason.LOW_MEMORY}, "Paused — low memory"),
    ],
)
def test_pill_text(changes: dict[str, object], expected: str) -> None:
    assert describe(status(**changes))[0] == expected


def test_pill_colour_follows_health() -> None:
    ok_colour = describe(status())[1]
    busy_colour = describe(status(health=Health.BUSY))[1]

    assert ok_colour != busy_colour


# Pausing --------------------------------------------------------------------------------------


class FakeMonitor:
    def __init__(self) -> None:
        self.reading = snapshot()

    def snapshot(self) -> SystemSnapshot:
        return self.reading


@pytest.fixture
def managers(
    qapp: QApplication,
    session_factory: Callable[[], Session],
) -> Generator[tuple[BackgroundManager, ProcessingManager, EmbeddingManager, FakeMonitor], None, None]:
    activity = ActivityManager(AsyncTaskExecutor(max_workers=1), session_factory)
    processing = ProcessingManager(AsyncTaskExecutor(max_workers=1), session_factory)
    embedding = EmbeddingManager(
        AsyncTaskExecutor(max_workers=1),
        session_factory,
        embedder_factory=lambda spec: FakeEmbedder(),
        preferences=UserPreferences(),
        save=lambda preferences: None,
    )
    monitor = FakeMonitor()
    background = BackgroundManager(
        activity, processing, embedding, monitor=monitor, session_factory=session_factory  # type: ignore[arg-type]
    )

    yield background, processing, embedding, monitor

    activity.shutdown()
    processing.shutdown()
    embedding.shutdown()


def test_user_can_pause_and_resume(managers) -> None:  # type: ignore[no-untyped-def]
    background, processing, embedding, _ = managers

    background.pause()
    assert processing.is_paused and embedding.is_paused
    assert background.status is not None
    assert background.status.pause_reason is PauseReason.USER

    background.resume()
    assert not processing.is_paused and not embedding.is_paused
    assert background.status.pause_reason is PauseReason.NONE


def test_low_memory_pauses_and_recovers_with_margin(managers) -> None:  # type: ignore[no-untyped-def]
    background, processing, embedding, monitor = managers

    monitor.reading = snapshot(available_mb=LOW_MEMORY_MB - 100)
    background.refresh()
    assert processing.is_paused and embedding.is_paused
    assert background.pause_reason is PauseReason.LOW_MEMORY

    # Just above the low mark is not enough to resume (no flickering).
    monitor.reading = snapshot(available_mb=LOW_MEMORY_MB + 100)
    background.refresh()
    assert processing.is_paused

    monitor.reading = snapshot(available_mb=RECOVERED_MEMORY_MB + 100)
    background.refresh()
    assert not processing.is_paused and not embedding.is_paused


def test_user_pause_survives_memory_recovery(managers) -> None:  # type: ignore[no-untyped-def]
    background, processing, _, monitor = managers

    background.pause()
    monitor.reading = snapshot(available_mb=LOW_MEMORY_MB - 100)
    background.refresh()
    monitor.reading = snapshot(available_mb=RECOVERED_MEMORY_MB + 500)
    background.refresh()

    assert processing.is_paused
    assert background.pause_reason is PauseReason.USER


def test_pill_is_wide_enough_for_its_text(qapp: QApplication) -> None:
    from PySide6.QtWidgets import QWidget

    from app.ui.widgets.status_pill import StatusPill

    host = QWidget()
    host.resize(1280, 800)
    pill = StatusPill(host)
    pill.show_status(status(imports_running=1, documents_to_read=12, meaning_done=1, meaning_total=9))

    text_width = pill._text.sizeHint().width()
    assert pill.width() >= text_width + 10 + 8  # dot and spacing
    assert pill.geometry().right() <= host.width()

