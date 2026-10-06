from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QVBoxLayout

from app.documents.supported_formats import SUPPORTED_EXTENSIONS
from app.ui.theme import tokens as t
from app.ui.widgets.common import (
    button,
    hbox,
    icon_label,
    icon_tile,
    label,
    repolish,
    type_badge,
)


class EmptyLibraryWidget(QFrame):
    """Shown when a workspace has no documents: a large drop zone."""

    add_files_requested = Signal()
    add_folder_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setProperty("surface", "dropzone")
        self.setMinimumHeight(420)

        tile = icon_tile("upload", t.ACCENT, t.ACCENT_SOFT, size=64, icon_size=30)

        title = label("Add your study material")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")

        message = label(
            "Drop files or a whole folder here. Large collections are fine — "
            "you can keep working while they are added.",
            "muted",
            wrap=True,
        )
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setMaximumWidth(460)

        add_files = button("Add files", "primary", "file", "#FFFFFF")
        add_files.clicked.connect(self.add_files_requested)

        add_folder = button("Add a folder", "secondary", "folder", t.INK)
        add_folder.clicked.connect(self.add_folder_requested)

        file_types = sorted(set(SUPPORTED_EXTENSIONS.values()), key=["pdf", "txt", "md"].index)

        formats = hbox(
            1,
            label("Supported:", "small"),
            *[type_badge(file_type) for file_type in file_types],
            label("· more formats will come as extensions", "small"),
            1,
            spacing=8,
        )

        privacy = hbox(
            1,
            icon_label("lock", t.MUTED, 14),
            label("Your files stay where they are. Nothing is uploaded.", "small"),
            1,
            spacing=6,
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(20)
        layout.addStretch(1)
        layout.addWidget(tile, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(title, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(message, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addLayout(hbox(1, add_files, add_folder, 1, spacing=10))
        layout.addLayout(formats)
        layout.addLayout(privacy)
        layout.addStretch(1)

    def set_drag_active(self, active: bool) -> None:
        self.setProperty("dragActive", "true" if active else "false")
        repolish(self)
