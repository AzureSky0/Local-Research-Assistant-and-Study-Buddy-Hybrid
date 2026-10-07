from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QFrame, QMessageBox, QVBoxLayout, QWidget

from app.core.computer_profile import ComputerProfile, detect_profile, total_memory_gb
from app.core.config import settings
from app.core.constants import DATA_DIR_ENV_VAR, LOG_FILENAME
from app.core.paths import DATA_DIR, LOG_DIR
from app.knowledge.embeddings.embedding_models import model_for_profile
from app.ui.managers.embedding_manager import EmbeddingManager
from app.ui.platform import open_folder
from app.ui.theme import tokens as t
from app.ui.widgets.common import button, hbox, label, vbox


class SettingsPage(QWidget):
    """Application information and data locations."""

    back_requested = Signal()

    def __init__(self, embedding: EmbeddingManager | None = None) -> None:
        super().__init__()
        self.setObjectName("page")
        self._embedding = embedding

        back = button("Back", "ghost", "chevron-left", t.MUTED)
        back.clicked.connect(self.back_requested)

        title = label("Settings", "title")

        computer_card = self._computer_card() if embedding is not None else None

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
            "Your local knowledge bank: find anything in your documents. Your files never leave your computer.",
            None,
            None,
        )

        content = QWidget()
        content.setObjectName("page")
        content.setMaximumWidth(760)
        content_layout = vbox(back, title, computer_card, data_card, logs_card, about_card, 1, spacing=16)
        content_layout.setAlignment(back, Qt.AlignmentFlag.AlignLeft)
        content_layout.setContentsMargins(48, 24, 48, 48)
        content.setLayout(content_layout)

        layout = hbox(content, 1, spacing=0)
        layout.setStretchFactor(content, 100)
        self.setLayout(layout)

    # Computer profile (Decision 037) ------------------------------------------------

    def _computer_card(self) -> QFrame:
        assert self._embedding is not None

        memory = total_memory_gb()
        detected = detect_profile(memory)
        memory_text = f"{memory:.0f} GB of memory" if memory else "an unknown amount of memory"

        self._profile_choice = QComboBox()
        self._profile_choice.addItem(f"Automatic ({detected.label})", None)
        self._profile_choice.addItem("Light — fastest, uses the least memory", ComputerProfile.LIGHT)
        self._profile_choice.addItem("Standard — better search, needs about 16 GB", ComputerProfile.STANDARD)
        self._profile_choice.setAccessibleName("Computer profile")
        self._select_current_profile()
        self._profile_choice.activated.connect(self._on_profile_chosen)

        self._profile_details = label("", "small", wrap=True)
        self._update_profile_details()

        card = QFrame()
        card.setProperty("surface", "card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(8)
        layout.addWidget(label("This computer", "heading"))
        layout.addWidget(
            label(
                f"This computer has {memory_text}. The profile decides which local models "
                "the app uses, so it stays fast on this machine.",
                "muted",
                wrap=True,
            )
        )
        layout.addWidget(self._profile_choice, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._profile_details)
        return card

    def _select_current_profile(self) -> None:
        assert self._embedding is not None
        current = None if self._embedding.is_automatic else self._embedding.profile
        self._profile_choice.setCurrentIndex(max(0, self._profile_choice.findData(current)))

    def _update_profile_details(self) -> None:
        assert self._embedding is not None
        spec = self._embedding.spec
        self._profile_details.setText(
            f"In use: {self._embedding.profile.label} profile. Search by meaning uses "
            f"{spec.label} (downloaded once, about {spec.download_mb} MB; everything runs offline)."
        )

    def _on_profile_chosen(self, index: int) -> None:
        assert self._embedding is not None
        choice = self._profile_choice.itemData(index)
        new_profile = choice if choice is not None else detect_profile()

        if model_for_profile(new_profile) != self._embedding.spec:
            answer = QMessageBox.question(
                self,
                "Change computer profile",
                f"Switching to the {new_profile.label} profile rebuilds search by meaning "
                "for all workspaces in the background. Word search keeps working meanwhile.\n\n"
                "Continue?",
                QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes,
                QMessageBox.StandardButton.Yes,
            )
            if answer != QMessageBox.StandardButton.Yes:
                self._select_current_profile()
                return

        self._embedding.set_profile(choice)
        self._update_profile_details()

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
