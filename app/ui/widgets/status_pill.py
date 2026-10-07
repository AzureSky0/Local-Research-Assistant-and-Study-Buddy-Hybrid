"""Bottom-right indicator of background work and computer health."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QPoint, Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.computer_profile import ComputerProfile
from app.core.system_monitor import Health
from app.ui.formatting import format_time_left, plural
from app.ui.managers.background_manager import BackgroundStatus, PauseReason
from app.ui.theme import tokens as t
from app.ui.widgets.common import button, hbox, label

MARGIN = 16

HEALTH_COLORS = {
    Health.OK: "#2E9E6A",
    Health.BUSY: "#C98A1B",
    Health.LOW_MEMORY: "#C2412D",
}
PAUSED_COLOR = "#8A8F9C"

PROFILE_CAPABILITY = {
    ComputerProfile.STANDARD: "Comfortable for search by meaning and, later, local AI models up to about 8B.",
    ComputerProfile.LIGHT: "Fast search; later, small local AI models (about 1–3B).",
}


def time_left(seconds: float | None, paused: bool) -> str:
    """The estimate shown next to a job, for example ' · about 6 minutes left'."""
    if paused:
        return ""
    return f" · {format_time_left(seconds)}" if seconds is not None else " · estimating time left…"


def describe(status: BackgroundStatus) -> tuple[str, str]:
    """Pill text and dot color for a status."""

    if status.pause_reason is PauseReason.USER:
        return "Background work paused", PAUSED_COLOR

    if status.pause_reason is PauseReason.LOW_MEMORY:
        return "Paused — low memory", HEALTH_COLORS[Health.LOW_MEMORY]

    color = HEALTH_COLORS[status.health]
    parts = []

    if status.imports_running:
        parts.append("Adding files")

    if status.documents_to_read:
        parts.append(f"Reading {plural(status.documents_to_read, 'document')}")

    # No percentage here: it covers all workspaces, while the Library shows
    # the open workspace's own progress. The panel has the details.
    if not status.meaning_unavailable and status.meaning_total and status.meaning_done < status.meaning_total:
        parts.append("Preparing search by meaning")

    if not parts:
        return "All caught up", color

    return " · ".join(parts), color


class _Dot(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(10, 10)
        self._color = QColor(HEALTH_COLORS[Health.OK])

    def set_color(self, color: str) -> None:
        self._color = QColor(color)
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._color)
        painter.drawEllipse(self.rect())


class StatusPill(QPushButton):
    """A small always-visible summary; click for details."""

    def __init__(self, host: QWidget) -> None:
        super().__init__(host)
        self.setObjectName("statusPill")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName("Background work and computer status")
        self.setStyleSheet(
            f"QPushButton#statusPill {{ background: {t.SURFACE}; border: 1px solid {t.BORDER};"
            f" border-radius: 16px; min-height: 32px; max-height: 32px; padding: 0; }}"
            f"QPushButton#statusPill:hover {{ border-color: {t.BORDER_STRONG}; }}"
        )

        self._dot = _Dot()
        self._text = QLabel("Starting…")
        self._text.setStyleSheet(f"color: {t.SUBTLE}; font-size: 12px; background: transparent;")
        for child in (self._dot, self._text):
            child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        layout = hbox(self._dot, self._text, spacing=8)
        layout.setContentsMargins(14, 0, 14, 0)
        self.setLayout(layout)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(20, 24, 33, 40))
        self.setGraphicsEffect(shadow)

        host.installEventFilter(self)

    @property
    def text_shown(self) -> str:
        return self._text.text()

    def show_status(self, status: BackgroundStatus) -> None:
        text, color = describe(status)
        self._text.setText(text)
        self._dot.set_color(color)
        self.setToolTip(text)
        self.reposition()

    def reposition(self) -> None:
        # A button does not size itself from its layout, so size it explicitly.
        layout = self.layout()
        if layout is not None:
            self.setFixedSize(layout.sizeHint().width(), 32)

        host = self.parentWidget()
        if host is not None:
            self.move(host.width() - self.width() - MARGIN, host.height() - self.height() - MARGIN)
            self.raise_()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Resize:
            self.reposition()
        return super().eventFilter(watched, event)


class StatusPanel(QFrame):
    """Details: background jobs, this app's usage, this computer, pause."""

    pause_requested = Signal()
    resume_requested = Signal()

    def __init__(self, parent: QWidget, profile: ComputerProfile) -> None:
        super().__init__(parent, Qt.WindowType.Popup)
        self.setObjectName("statusPanel")
        self.setFixedWidth(340)
        self.setStyleSheet(
            f"QFrame#statusPanel {{ background: {t.SURFACE}; border: 1px solid {t.BORDER};"
            " border-radius: 12px; }"
        )
        self._paused = False

        self._jobs = label("", wrap=True)
        self._meaning_bar = QProgressBar()
        self._meaning_bar.setTextVisible(False)
        self._meaning_label = label("", wrap=True)
        self._idle = label("All caught up — nothing running.", wrap=True)
        self._note = label("", "small", wrap=True)

        self._pause_button = button("Pause background work", None, size="small")
        self._pause_button.clicked.connect(self._toggle_pause)

        self._app_usage = label("", "small")
        self._memory_bar = QProgressBar()
        self._memory_bar.setTextVisible(False)
        self._memory_label = label("", "small")
        self._cpu_bar = QProgressBar()
        self._cpu_bar.setTextVisible(False)
        self._cpu_label = label("", "small")

        profile_text = label(
            f"{profile.label} profile — {PROFILE_CAPABILITY[profile]}", "small", wrap=True
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)
        layout.addWidget(label("Background work", "heading"))
        layout.addWidget(self._idle)
        layout.addWidget(self._jobs)
        layout.addWidget(self._meaning_label)
        layout.addWidget(self._meaning_bar)
        layout.addWidget(self._note)
        layout.addWidget(self._pause_button, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addSpacing(6)
        layout.addWidget(label("This app", "heading"))
        layout.addWidget(self._app_usage)
        layout.addSpacing(6)
        layout.addWidget(label("This computer", "heading"))
        layout.addWidget(self._memory_label)
        layout.addWidget(self._memory_bar)
        layout.addWidget(self._cpu_label)
        layout.addWidget(self._cpu_bar)
        layout.addWidget(profile_text)

    def show_status(self, status: BackgroundStatus) -> None:
        self._paused = status.pause_reason is not PauseReason.NONE

        jobs = []
        if status.imports_running:
            jobs.append(
                f"Adding files: {plural(status.imports_running, 'import')} running"
                + time_left(status.imports_seconds_left, paused=False)
            )
        if status.documents_to_read:
            jobs.append(
                f"Reading: {plural(status.documents_to_read, 'document')} to go"
                + time_left(status.reading_seconds_left, self._paused)
            )
        self._jobs.setText("\n".join(jobs))
        self._jobs.setVisible(bool(jobs))

        # Only work still to do is listed; finished tasks disappear.
        meaning_running = (
            not status.meaning_unavailable and status.meaning_done < status.meaning_total
        )
        if meaning_running:
            percent = status.meaning_done * 100 // status.meaning_total
            self._meaning_label.setText(
                f"Preparing search by meaning: {percent}%"
                + time_left(status.meaning_seconds_left, self._paused)
            )
            self._meaning_bar.setRange(0, status.meaning_total)
            self._meaning_bar.setValue(status.meaning_done)
        elif status.meaning_unavailable:
            self._meaning_label.setText("Search by meaning is unavailable — word search still works.")
        self._meaning_label.setVisible(meaning_running or status.meaning_unavailable)
        self._meaning_bar.setVisible(meaning_running)

        has_work = bool(jobs) or meaning_running
        self._idle.setVisible(not has_work and not status.meaning_unavailable)
        self._pause_button.setVisible(has_work or self._paused)

        notes = {
            PauseReason.USER: "Paused by you. Nothing is lost; work continues when you resume.",
            PauseReason.LOW_MEMORY: "Paused automatically because the computer is low on memory. "
            "It resumes on its own when memory frees up.",
        }
        note = notes.get(status.pause_reason)
        if note is None and status.health is Health.BUSY:
            note = "Your computer is busy, so background work may go more slowly."
        self._note.setVisible(note is not None)
        self._note.setText(note or "")

        self._pause_button.setText("Resume background work" if self._paused else "Pause background work")
        self._pause_button.setEnabled(status.pause_reason is not PauseReason.LOW_MEMORY)

        snapshot = status.snapshot
        if snapshot is not None:
            self._app_usage.setText(
                f"Memory {snapshot.app_memory_mb / 1024:.1f} GB · CPU {snapshot.app_cpu_percent:.0f}%"
            )
            self._memory_bar.setRange(0, 100)
            self._memory_bar.setValue(round(snapshot.memory_used_percent))
            self._memory_label.setText(
                f"Memory: {snapshot.memory_used_mb / 1024:.1f} of {snapshot.memory_total_mb / 1024:.1f} GB used"
            )
            self._cpu_bar.setRange(0, 100)
            self._cpu_bar.setValue(round(snapshot.system_cpu_percent))
            self._cpu_label.setText(f"CPU: {snapshot.system_cpu_percent:.0f}% busy")

        self.adjustSize()

    def show_above(self, anchor: QWidget) -> None:
        self.adjustSize()
        bottom_right = anchor.mapToGlobal(QPoint(anchor.width(), 0))
        self.move(bottom_right.x() - self.width(), bottom_right.y() - self.height() - 8)
        self.show()

    def _toggle_pause(self) -> None:
        if self._paused:
            self.resume_requested.emit()
        else:
            self.pause_requested.emit()
