from __future__ import annotations

from pathlib import Path
from uuid import UUID

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QProgressBar,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.documents.dto.document_import_result import DocumentImportStatus
from app.ui.formatting import format_duration, format_time_left, plural
from app.ui.managers.activity_manager import ActivityManager, ActivityState, ImportActivity
from app.ui.theme import mono_font
from app.ui.theme import tokens as t
from app.ui.widgets.common import clear_layout, button, hbox, label, vbox

MAX_LISTED_ISSUES = 50

ISSUE_LOOKS: dict[DocumentImportStatus, tuple[str, t.Swatch]] = {
    DocumentImportStatus.FAILED: ("Couldn’t add", t.STATUS_PROBLEM),
    DocumentImportStatus.UNSUPPORTED: ("Not supported yet", t.STATUS_NEUTRAL),
    DocumentImportStatus.ALREADY_IMPORTED: ("Already here", t.STATUS_NEUTRAL),
}

SUMMARY_TILES: list[tuple[DocumentImportStatus, str, t.Swatch]] = [
    (DocumentImportStatus.IMPORTED, "Added", t.STATUS_READY),
    (DocumentImportStatus.ALREADY_IMPORTED, "Already here", t.STATUS_NEUTRAL),
    (DocumentImportStatus.UNSUPPORTED, "Not supported yet", t.STATUS_NEUTRAL),
    (DocumentImportStatus.FAILED, "Couldn’t add", t.STATUS_PROBLEM),
]


def friendly_reason(status: DocumentImportStatus, error: str | None) -> str:
    """Short, plain-language reason for an import issue."""

    if status is DocumentImportStatus.ALREADY_IMPORTED:
        return "The same file is already in this workspace."

    if status is DocumentImportStatus.UNSUPPORTED:
        return "This format isn’t supported yet — it may come as an extension."

    if error and " cannot be imported: " in error:
        reason = error.split(" cannot be imported: ", 1)[1]
        return reason[:1].upper() + reason[1:]

    return error or "Something went wrong."


class ActivityCard(QFrame):
    """One import: live progress while running, a summary when done."""

    cancel_requested = Signal(object)  # UUID
    open_library_requested = Signal(str)  # workspace id

    def __init__(self, activity: ImportActivity) -> None:
        super().__init__()
        self.setProperty("surface", "card")
        self._activity_id = activity.id
        self._workspace_id = activity.workspace_id

        self._title = label("", "heading")
        self._subtitle = label("", "small")

        self._cancel = button("Cancel", None, size="small")
        self._cancel.clicked.connect(lambda: self.cancel_requested.emit(self._activity_id))

        self._open_library = button("Open Library", None, size="small")
        self._open_library.clicked.connect(
            lambda: self.open_library_requested.emit(self._workspace_id)
        )

        # Running section
        self._counter = QLabel()
        self._percent = QLabel()
        self._percent.setFont(mono_font(13))
        self._percent.setStyleSheet(f"color: {t.MUTED};")
        self._progress = QProgressBar()
        self._progress.setTextVisible(False)
        self._progress.setAccessibleName("Import progress")
        self._current = label("", "small")
        self._running_counts = label("", "small")

        self._running = QWidget()
        self._running.setLayout(
            vbox(
                hbox(self._counter, 1, self._percent),
                self._progress,
                self._current,
                self._running_counts,
                spacing=8,
            )
        )

        # Finished section
        self._tiles = QGridLayout()
        self._tiles.setSpacing(10)
        self._issues = QVBoxLayout()
        self._issues.setSpacing(0)

        self._issues_box = QFrame()
        self._issues_box.setStyleSheet(
            f"QFrame#issues {{ border: 1px solid {t.DIVIDER}; border-radius: 10px; }}"
        )
        self._issues_box.setObjectName("issues")
        issues_title = label("Needs your attention")
        issues_title.setStyleSheet("font-weight: 600; font-size: 13px; padding: 10px 14px;")
        issues_layout = QVBoxLayout(self._issues_box)
        issues_layout.setContentsMargins(0, 0, 0, 0)
        issues_layout.setSpacing(0)
        issues_layout.addWidget(issues_title)
        issues_layout.addLayout(self._issues)

        self._finished = QWidget()
        self._finished.setLayout(vbox(self._tiles, self._issues_box, spacing=16))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)
        layout.addLayout(
            hbox(vbox(self._title, self._subtitle, spacing=4), 1, self._cancel, self._open_library)
        )
        layout.addWidget(self._running)
        layout.addWidget(self._finished)

        self.update_activity(activity)

    def update_activity(self, activity: ImportActivity) -> None:
        running = activity.is_running

        self._cancel.setVisible(running)
        self._open_library.setVisible(not running)
        self._running.setVisible(running)
        self._finished.setVisible(not running)

        if running:
            self._show_running(activity)
        else:
            self._show_finished(activity)

    def _show_running(self, activity: ImportActivity) -> None:
        self._title.setText(activity.title)

        left = activity.seconds_left
        subtitle = activity.workspace_name
        if left is not None:
            subtitle += f" · {format_time_left(left)}"
        self._subtitle.setText(subtitle)

        if activity.total > 0:
            self._progress.setRange(0, activity.total)
            self._progress.setValue(activity.done)
            self._counter.setText(f"{activity.done} of {plural(activity.total, 'file')}")
            self._percent.setText(f"{int(activity.done / activity.total * 100)}%")
        else:
            self._progress.setRange(0, 0)  # busy indicator while scanning
            self._counter.setText("Looking for documents…")
            self._percent.setText("")

        self._current.setText(f"Now: {activity.current_item}" if activity.done else "")

        added = activity.count(DocumentImportStatus.IMPORTED)
        duplicates = activity.count(DocumentImportStatus.ALREADY_IMPORTED)
        problems = activity.count(DocumentImportStatus.FAILED) + activity.count(
            DocumentImportStatus.UNSUPPORTED
        )
        self._running_counts.setText(
            f"{added} added · {duplicates} already in this workspace · {problems} skipped"
        )

    def _show_finished(self, activity: ImportActivity) -> None:
        added = activity.count(DocumentImportStatus.IMPORTED)

        if activity.state is ActivityState.FAILED:
            self._title.setText("Import stopped because of an error")
        elif activity.state is ActivityState.CANCELLED:
            self._title.setText(f"Stopped — added {plural(added, 'file')}")
        else:
            self._title.setText(f"Added {plural(added, 'file')}")

        duration = (activity.finished_at or activity.started_at) - activity.started_at
        self._subtitle.setText(f"{activity.workspace_name} · took {format_duration(duration)}")

        self._fill_tiles(activity)
        self._fill_issues(activity)

    def _fill_tiles(self, activity: ImportActivity) -> None:
        clear_layout(self._tiles)

        for column, (status, text, swatch) in enumerate(SUMMARY_TILES):
            count = QLabel(str(activity.count(status)))
            count.setFont(mono_font(22))
            count.setStyleSheet(f"color: {swatch.color}; font-weight: 600;")
            caption = label(text)
            caption.setStyleSheet(f"color: {swatch.color}; font-size: 13px;")

            tile = QFrame()
            tile.setStyleSheet(f"background: {swatch.tint}; border-radius: 10px;")
            tile_layout = vbox(count, caption, spacing=2)
            tile_layout.setContentsMargins(14, 12, 14, 12)
            tile.setLayout(tile_layout)
            self._tiles.addWidget(tile, 0, column)

    def _fill_issues(self, activity: ImportActivity) -> None:
        clear_layout(self._issues)

        issues = [
            result for result in activity.results if result.status in ISSUE_LOOKS
        ]
        issues.sort(key=lambda result: list(ISSUE_LOOKS).index(result.status))

        if activity.error:
            self._issues.addWidget(self._issue_row("Error", t.STATUS_PROBLEM, "", activity.error))

        for result in issues[:MAX_LISTED_ISSUES]:
            kind, swatch = ISSUE_LOOKS[result.status]
            self._issues.addWidget(
                self._issue_row(
                    kind,
                    swatch,
                    Path(result.file_path).name,
                    friendly_reason(result.status, result.error),
                )
            )

        if len(issues) > MAX_LISTED_ISSUES:
            more = label(f"…and {len(issues) - MAX_LISTED_ISSUES} more", "small")
            more.setContentsMargins(14, 10, 14, 10)
            self._issues.addWidget(more)

        self._issues_box.setVisible(bool(issues) or bool(activity.error))

    @staticmethod
    def _issue_row(kind: str, swatch: t.Swatch, file_name: str, reason: str) -> QWidget:
        chip = label(kind, "chip")
        chip.setStyleSheet(f"background: {swatch.tint}; color: {swatch.color};")

        name = QLabel(file_name)
        name.setFont(mono_font(12))
        name.setMinimumWidth(220)
        name.setMaximumWidth(280)
        name.setToolTip(file_name)

        reason_label = label(reason, "small", wrap=True)

        row = QWidget()
        row.setStyleSheet(f"border-top: 1px solid {t.DIVIDER};")
        chip.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        row_layout = hbox(chip, name, reason_label, spacing=14)
        row_layout.setStretchFactor(reason_label, 1)
        row_layout.setAlignment(chip, Qt.AlignmentFlag.AlignTop)
        row_layout.setAlignment(name, Qt.AlignmentFlag.AlignTop)
        row_layout.setContentsMargins(14, 10, 14, 10)
        row.setLayout(row_layout)

        for child in (chip, name, reason_label):
            child.setStyleSheet(child.styleSheet() + " border: none;")

        return row


class ActivityPage(QWidget):
    """Background work: running imports and their results."""

    open_library_requested = Signal(str)  # workspace id

    def __init__(self, activity: ActivityManager) -> None:
        super().__init__()
        self.setObjectName("page")
        self._activity = activity
        self._cards: dict[UUID, ActivityCard] = {}

        title = label("Activity", "title")
        intro = label(
            "Work running in the background. You can keep using the app while it runs.",
            "muted",
        )

        self._clear_button = button("Clear finished", None, size="small")
        self._clear_button.clicked.connect(self._clear_finished)

        self._running_title = label("RUNNING", "section")
        self._running_list = QVBoxLayout()
        self._running_list.setSpacing(12)

        self._finished_title = label("FINISHED", "section")
        self._finished_list = QVBoxLayout()
        self._finished_list.setSpacing(12)

        self._empty = label("Nothing running. Imports you start will appear here.", "muted")

        content = QWidget()
        content.setObjectName("page")
        content.setMaximumWidth(920)
        content_layout = vbox(
            hbox(vbox(title, intro, spacing=4), 1, self._clear_button),
            self._empty,
            self._running_title,
            self._running_list,
            self._finished_title,
            self._finished_list,
            1,
            spacing=16,
        )
        content_layout.setContentsMargins(48, 28, 48, 48)
        content.setLayout(content_layout)

        holder = QWidget()
        holder.setObjectName("page")
        holder_layout = hbox(content, 1, spacing=0)
        holder_layout.setStretchFactor(content, 100)
        holder.setLayout(holder_layout)

        scroll = QScrollArea()
        scroll.setObjectName("page")
        scroll.setWidgetResizable(True)
        scroll.setWidget(holder)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

        activity.activity_started.connect(self._add_card)
        activity.activity_updated.connect(self._update_card)
        activity.activity_finished.connect(self._finish_card)

        for existing in reversed(activity.activities):
            self._add_card(existing)

        self._update_sections()

    def _add_card(self, activity: ImportActivity) -> None:
        card = ActivityCard(activity)
        card.cancel_requested.connect(self._activity.cancel)
        card.open_library_requested.connect(self.open_library_requested)
        self._cards[activity.id] = card

        target = self._running_list if activity.is_running else self._finished_list
        target.insertWidget(0, card)
        self._update_sections()

    def _update_card(self, activity: ImportActivity) -> None:
        card = self._cards.get(activity.id)
        if card is not None:
            card.update_activity(activity)

    def _finish_card(self, activity: ImportActivity) -> None:
        card = self._cards.get(activity.id)
        if card is None:
            return

        self._running_list.removeWidget(card)
        self._finished_list.insertWidget(0, card)
        card.update_activity(activity)
        self._update_sections()

    def _clear_finished(self) -> None:
        self._activity.clear_finished()

        for activity_id in list(self._cards):
            card = self._cards[activity_id]
            if self._finished_list.indexOf(card) != -1:
                self._finished_list.removeWidget(card)
                card.deleteLater()
                del self._cards[activity_id]

        self._update_sections()

    def _update_sections(self) -> None:
        running = self._running_list.count()
        finished = self._finished_list.count()

        self._running_title.setVisible(running > 0)
        self._finished_title.setVisible(finished > 0)
        self._clear_button.setVisible(finished > 0)
        self._empty.setVisible(running == 0 and finished == 0)
