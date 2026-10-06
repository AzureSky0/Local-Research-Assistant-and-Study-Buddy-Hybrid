from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout

from app.documents.domain import Document
from app.ui.formatting import format_size, format_timestamp
from app.ui.platform import show_in_folder
from app.ui.theme import mono_font
from app.ui.theme import tokens as t
from app.ui.widgets.common import clear_layout, StatusChip, button, label, type_badge, vbox


class DocumentDetailsPanel(QFrame):
    """Details and actions for the selected document."""

    remove_requested = Signal(object)  # Document

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
        self._added = QLabel()

        facts = QGridLayout()
        facts.setHorizontalSpacing(12)
        facts.setVerticalSpacing(2)
        facts.addWidget(label("Size", "small"), 0, 0)
        facts.addWidget(label("Added", "small"), 0, 1)
        facts.addWidget(self._size, 1, 0)
        facts.addWidget(self._added, 1, 1)

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
        layout.addLayout(facts)
        layout.addLayout(vbox(label("Location", "small"), self._location, spacing=6))
        layout.addWidget(reveal, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addStretch(1)
        layout.addWidget(divider)
        layout.addWidget(remove, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(note)

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
        self._added.setText(format_timestamp(document.imported_at))
        self._location.setText(document.original_path)

    def _reveal(self) -> None:
        if self._document is not None:
            show_in_folder(Path(self._document.original_path))
