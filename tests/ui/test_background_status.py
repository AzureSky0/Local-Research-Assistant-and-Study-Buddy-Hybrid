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
        ({"pause_reason": PauseReason.LOW_MEMORY, "documents_to_read": 3}, "Paused — low memory"),
        ({"pause_reason": PauseReason.LOW_MEMORY}, "All caught up"),
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


def test_panel_shows_time_left(qapp: QApplication) -> None:
    from PySide6.QtWidgets import QWidget

    from app.core.computer_profile import ComputerProfile
    from app.ui.widgets.status_pill import StatusPanel

    host = QWidget()
    panel = StatusPanel(host, ComputerProfile.STANDARD)

    panel.show_status(
        status(
            documents_to_read=3,
            reading_seconds_left=90,
            meaning_done=40,
            meaning_total=100,
            meaning_seconds_left=360,
        )
    )
    assert "about 2 minutes left" in panel._jobs.text()
    assert panel._meaning_label.text() == "Preparing search by meaning: 40% · about 6 minutes left"

    # Not enough measured yet.
    panel.show_status(status(meaning_done=40, meaning_total=100))
    assert "estimating time left" in panel._meaning_label.text()

    # No estimate while paused.
    panel.show_status(
        status(
            pause_reason=PauseReason.USER,
            meaning_done=40,
            meaning_total=100,
            meaning_seconds_left=360,
        )
    )
    assert "left" not in panel._meaning_label.text()


def test_panel_lists_only_unfinished_work(qapp: QApplication) -> None:
    from PySide6.QtWidgets import QWidget

    from app.core.computer_profile import ComputerProfile
    from app.ui.widgets.status_pill import StatusPanel

    host = QWidget()
    panel = StatusPanel(host, ComputerProfile.STANDARD)

    panel.show_status(status(documents_to_read=2, meaning_done=40, meaning_total=100))
    assert panel._jobs.isVisibleTo(panel)
    assert panel._meaning_label.isVisibleTo(panel)
    assert not panel._idle.isVisibleTo(panel)

    # Reading finished; meaning still going.
    panel.show_status(status(meaning_done=90, meaning_total=100))
    assert not panel._jobs.isVisibleTo(panel)
    assert panel._meaning_label.isVisibleTo(panel)

    # Everything finished.
    panel.show_status(status())
    assert not panel._meaning_label.isVisibleTo(panel)
    assert not panel._meaning_bar.isVisibleTo(panel)
    assert not panel._pause_button.isVisibleTo(panel)
    assert panel._idle.isVisibleTo(panel)


def test_panel_never_cuts_off_wrapped_text(qapp: QApplication) -> None:
    from PySide6.QtWidgets import QLabel, QWidget

    from app.core.computer_profile import ComputerProfile
    from app.ui.widgets.status_pill import StatusPanel

    host = QWidget()
    panel = StatusPanel(host, ComputerProfile.STANDARD)
    panel.show_status(
        status(
            imports_running=1,
            imports_seconds_left=30,
            documents_to_read=4,
            reading_seconds_left=50,
            meaning_done=25,
            meaning_total=100,
            meaning_seconds_left=70,
        )
    )
    panel.show_above(host)
    qapp.processEvents()

    for text in panel.findChildren(QLabel):
        if text.isVisible() and text.wordWrap():
            assert text.height() >= text.heightForWidth(text.width()), text.text()
    panel.hide()


def test_low_memory_with_nothing_to_do_is_not_an_alarm(qapp: QApplication) -> None:
    from PySide6.QtWidgets import QWidget

    from app.core.computer_profile import ComputerProfile
    from app.ui.widgets.status_pill import StatusPanel

    idle = status(pause_reason=PauseReason.LOW_MEMORY, health=Health.LOW_MEMORY)
    text, color = describe(idle)
    assert text == "All caught up"
    assert color != describe(status(pause_reason=PauseReason.LOW_MEMORY, documents_to_read=2))[1]

    host = QWidget()
    panel = StatusPanel(host, ComputerProfile.LIGHT)
    panel.show_status(idle)
    assert "Nothing is waiting" in panel._note.text()
    assert not panel._pause_button.isVisibleTo(panel)

    # With work waiting, it is a real pause.
    assert describe(status(pause_reason=PauseReason.LOW_MEMORY, documents_to_read=2))[0] == "Paused — low memory"
