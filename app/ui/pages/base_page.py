from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)


class BasePage(QWidget):
    """
    Base class for all application pages.

    Provides:
    - Page title
    - Main layout
    - Content layout for child widgets
    - Consistent spacing and margins
    """

    def __init__(self, title: str) -> None:
        super().__init__()

        self._setup_layout()
        self._setup_title(title)

    def _setup_layout(self) -> None:
        """Create the page layouts."""

        self.main_layout = QVBoxLayout(self)

        self.main_layout.setContentsMargins(
            24,
            24,
            24,
            24,
        )

        self.main_layout.setSpacing(16)

        self.content_layout = QVBoxLayout()

        self.content_layout.setSpacing(12)

    def _setup_title(self, title: str) -> None:
        """Create the page title."""

        self.title_label = QLabel(title)

        self.title_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.main_layout.addWidget(self.title_label)

        self.main_layout.addLayout(
            self.content_layout
        )