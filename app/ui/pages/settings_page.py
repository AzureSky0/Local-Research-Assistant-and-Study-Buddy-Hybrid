from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget

from app.core.config import settings
from app.core.constants import DATA_DIR_ENV_VAR, LOG_FILENAME
from app.core.paths import DATA_DIR, LOG_DIR
from app.ui.platform import open_folder
from app.ui.theme import tokens as t
from app.ui.widgets.common import button, hbox, label, vbox


class SettingsPage(QWidget):
    """Application information and data locations."""

    back_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("page")

        back = button("Back", "ghost", "chevron-left", t.MUTED)
        back.clicked.connect(self.back_requested)

        title = label("Settings", "title")

        data_card = self._card(
            "Your data",
            "Workspaces and the document library are stored on this computer in:",
            str(DATA_DIR),
            f"Change this location by setting the {DATA_DIR_ENV_VAR} environment variable.",
            "Open data folder",
            lambda: open_folder(DATA_DIR),
        )

        logs_card = self._card(
            "Logs",
            "If something goes wrong, the log file helps find the cause:",
            str(LOG_DIR / LOG_FILENAME),
            None,
            "Open logs folder",
            lambda: open_folder(LOG_DIR),
        )

        about_card = self._card(
            "About",
            f"{settings.app_name}",
            f"Version {settings.app_version}",
            "A local-first study and research workspace. Your files never leave your computer.",
            None,
            None,
        )

        content = QWidget()
        content.setObjectName("page")
        content.setMaximumWidth(760)
        content_layout = vbox(back, title, data_card, logs_card, about_card, 1, spacing=16)
        content_layout.setAlignment(back, Qt.AlignmentFlag.AlignLeft)
        content_layout.setContentsMargins(48, 24, 48, 48)
        content.setLayout(content_layout)

        layout = hbox(content, 1, spacing=0)
        layout.setStretchFactor(content, 100)
        self.setLayout(layout)

    @staticmethod
    def _card(
        heading: str,
        text: str,
        value: str,
        note: str | None,
        action_text: str | None,
        action,  # type: ignore[no-untyped-def]
    ) -> QFrame:
        card = QFrame()
        card.setProperty("surface", "card")

        value_label = label(value, "mono", wrap=True)
        value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(8)
        layout.addWidget(label(heading, "heading"))
        layout.addWidget(label(text, "muted", wrap=True))
        layout.addWidget(value_label)

        if note:
            layout.addWidget(label(note, "small", wrap=True))

        if action_text and action:
            action_button = button(action_text, None, "folder", t.INK, size="small")
            action_button.clicked.connect(action)
            layout.addSpacing(4)
            layout.addWidget(action_button, 0, Qt.AlignmentFlag.AlignLeft)

        return card
