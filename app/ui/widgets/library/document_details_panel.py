from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout

from app.documents.domain import Document, DocumentProcessingStatus
from app.ui.formatting import format_size, format_timestamp
from app.ui.platform import show_in_folder
from app.ui.theme import mono_font
from app.ui.theme import tokens as t
from app.ui.widgets.common import clear_layout, StatusChip, button, label, type_badge, vbox


class DocumentDetailsPanel(QFrame):
    """Details and actions for the selected document."""

    remove_requested = Signal(object)  # Document
    retry_requested = Signal(object)  # Document

    def __init__(self) -> None:
        super().__init__()
        self.setProperty("surface", "panel")
        self.setFixedWidth(320)

        self._document: Document | None = None

        self._badge_holder = QVBoxLayout()
        self._badge_holder.setContentsMargins(0, 0, 0, 0)

        self._name = label("", wrap=True)
        self._name.setStyleSheet("font-size: 18px; font-weight: 600;")
        self._name.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self._status = StatusChip()

        self._size = QLabel()
        self._size.setFont(mono_font(13))
        self._pages = QLabel()
        self._pages.setFont(mono_font(13))
        self._added = QLabel()

        facts = QGridLayout()
        facts.setHorizontalSpacing(12)
        facts.setVerticalSpacing(2)
        facts.addWidget(label("Size", "small"), 0, 0)
        facts.addWidget(label("Pages", "small"), 0, 1)
        facts.addWidget(label("Added", "small"), 0, 2)
        facts.addWidget(self._size, 1, 0)
        facts.addWidget(self._pages, 1, 1)
        facts.addWidget(self._added, 1, 2)

        # Shown when the document could not be read.
        self._problem = QFrame()
        self._problem.setObjectName("problem")
        self._problem.setStyleSheet(
            f"QFrame#problem {{ background: {t.STATUS_PROBLEM.tint}; border-radius: 10px; }}"
        )
        self._problem_text = label("", wrap=True)
        self._problem_text.setStyleSheet(f"color: {t.STATUS_PROBLEM.color}; font-size: 13px;")
        retry = button("Try again", None, size="small")
        retry.clicked.connect(lambda: self.retry_requested.emit(self._document))
        problem_layout = QVBoxLayout(self._problem)
        problem_layout.setContentsMargins(14, 12, 14, 12)
        problem_layout.setSpacing(10)
        problem_layout.addWidget(self._problem_text)
        problem_layout.addWidget(retry, 0, Qt.AlignmentFlag.AlignLeft)

        self._location = label("", "mono", wrap=True)
        self._location.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        reveal = button("Show in folder", None, "folder", t.INK, size="small")
        reveal.clicked.connect(self._reveal)

        remove = button("Remove from workspace", "danger", "trash", t.DANGER)
        remove.clicked.connect(lambda: self.remove_requested.emit(self._document))

        note = label("The original file stays on your computer.", "small", wrap=True)

        divider = QFrame()
        divider.setProperty("surface", "divider")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 28, 24, 28)
        layout.setSpacing(20)
        layout.addLayout(self._badge_holder)
        layout.addWidget(self._name)
        layout.addWidget(self._status, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._problem)
        layout.addLayout(facts)
        layout.addLayout(vbox(label("Location", "small"), self._location, spacing=6))
        layout.addWidget(reveal, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addStretch(1)
        layout.addWidget(divider)
        layout.addWidget(remove, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(note)

    @property
    def document(self) -> Document | None:
        return self._document if self.isVisible() else None

    def show_document(self, document: Document | None) -> None:
        self._document = document
        self.setVisible(document is not None)

        if document is None:
            return

        clear_layout(self._badge_holder)

        self._badge_holder.addWidget(type_badge(document.file_type), 0, Qt.AlignmentFlag.AlignLeft)

        self._name.setText(document.file_name)
        self._status.set_status(document.processing_status)
        self._size.setText(format_size(document.file_size))
        self._pages.setText(str(document.page_count) if document.page_count else "—")

        failed = document.processing_status is DocumentProcessingStatus.FAILED
        self._problem.setVisible(failed)
        self._problem_text.setText(document.processing_error or "This document could not be read.")
        self._added.setText(format_timestamp(document.imported_at))
        self._location.setText(document.original_path)

    def _reveal(self) -> None:
        if self._document is not None:
            show_in_folder(Path(self._document.original_path))
