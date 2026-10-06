"""Small building blocks shared by every screen."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.documents.domain import DocumentProcessingStatus
from app.ui.theme import tokens as t
from app.ui.theme.icons import icon, icon_pixmap


def label(text: str = "", role: str | None = None, wrap: bool = False) -> QLabel:
    """Create a label with an optional text role from the stylesheet."""

    widget = QLabel(text)

    if role is not None:
        widget.setProperty("role", role)

    widget.setWordWrap(wrap)
    return widget


def button(
    text: str,
    variant: str | None = None,
    icon_name: str | None = None,
    icon_color: str = t.INK,
    size: str | None = None,
) -> QPushButton:
    """Create a push button styled by its variant."""

    widget = QPushButton(text)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)

    if variant is not None:
        widget.setProperty("variant", variant)

    if size is not None:
        widget.setProperty("size", size)

    if icon_name is not None:
        widget.setIcon(icon(icon_name, icon_color))
        widget.setIconSize(QSize(18, 18))

    return widget


def icon_label(name: str, color: str, size: int = 18) -> QLabel:
    """A label showing only an icon."""

    widget = QLabel()
    widget.setPixmap(icon_pixmap(name, color, size))
    widget.setFixedSize(size, size)
    return widget


def icon_tile(name: str, color: str, tint: str, size: int = 40, icon_size: int = 20) -> QLabel:
    """A rounded tinted square with an icon, used for workspaces."""

    widget = QLabel()
    widget.setPixmap(icon_pixmap(name, color, icon_size))
    widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
    widget.setFixedSize(size, size)
    widget.setStyleSheet(f"background: {tint}; border-radius: {size // 4}px;")
    return widget


def hbox(*items: QWidget | QLayout | int | None, spacing: int = 8, margins: int = 0) -> QHBoxLayout:
    """Horizontal layout. An int adds stretch; None is skipped."""

    layout = QHBoxLayout()
    _fill(layout, items, spacing, margins)
    return layout


def vbox(*items: QWidget | QLayout | int | None, spacing: int = 8, margins: int = 0) -> QVBoxLayout:
    """Vertical layout. An int adds stretch; None is skipped."""

    layout = QVBoxLayout()
    _fill(layout, items, spacing, margins)
    return layout


def _fill(
    layout: QHBoxLayout | QVBoxLayout,
    items: tuple[QWidget | QLayout | int | None, ...],
    spacing: int,
    margins: int,
) -> None:
    layout.setSpacing(spacing)
    layout.setContentsMargins(margins, margins, margins, margins)

    for item in items:
        if item is None:
            continue
        if isinstance(item, int):
            layout.addStretch(item)
        elif isinstance(item, QLayout):
            layout.addLayout(item)
        else:
            layout.addWidget(item)


def surface(kind: str) -> QFrame:
    """A frame styled as a card, panel, sidebar, header or drop zone."""

    frame = QFrame()
    frame.setProperty("surface", kind)
    return frame


def clear_layout(layout: QLayout) -> None:
    """Remove and delete every widget in a layout."""

    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget() if item is not None else None

        if widget is not None:
            widget.hide()
            widget.deleteLater()


class SearchField(QFrame):
    """A text field with a leading search icon."""

    def __init__(self, placeholder: str) -> None:
        super().__init__()
        self.setProperty("surface", "input")
        self.setMinimumHeight(40)

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.setProperty("embedded", "true")
        self.input.setAccessibleName(placeholder)

        self._clear = QPushButton()
        self._clear.setProperty("variant", "ghost")
        self._clear.setIcon(icon("close", t.MUTED, 14, 2.5))
        self._clear.setFixedSize(28, 28)
        self._clear.setToolTip("Clear search")
        self._clear.setAccessibleName("Clear search")
        self._clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear.clicked.connect(self.clear)
        self._clear.hide()
        self.input.textChanged.connect(lambda text: self._clear.setVisible(bool(text)))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 6, 0)
        layout.setSpacing(8)
        layout.addWidget(icon_label("search", t.MUTED, 16))
        layout.addWidget(self.input, 1)
        layout.addWidget(self._clear)

    def text(self) -> str:
        return self.input.text()

    def clear(self) -> None:
        self.input.clear()
        self.input.setFocus()


def repolish(widget: QWidget) -> None:
    """Re-apply the stylesheet after a dynamic property changed."""

    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


# Document status presentation ----------------------------------------------


@dataclass(frozen=True, slots=True)
class StatusLook:
    """How a document status is shown: words, icon and colors."""

    label: str
    icon: str
    swatch: t.Swatch
    group: str  # filter group: ready | in_progress | attention


STATUS_LOOKS: dict[DocumentProcessingStatus, StatusLook] = {
    DocumentProcessingStatus.PENDING: StatusLook("Queued", "clock", t.STATUS_NEUTRAL, "in_progress"),
    DocumentProcessingStatus.PROCESSING: StatusLook("Reading…", "spinner", t.STATUS_IN_PROGRESS, "in_progress"),
    DocumentProcessingStatus.READY: StatusLook("Ready", "check", t.STATUS_READY, "ready"),
    DocumentProcessingStatus.FAILED: StatusLook("Couldn’t read", "alert", t.STATUS_PROBLEM, "attention"),
    DocumentProcessingStatus.CANCELLED: StatusLook("Stopped", "stop", t.STATUS_NEUTRAL, "attention"),
}


class StatusChip(QWidget):
    """A rounded status label with an icon (never color alone)."""

    def __init__(self, status: DocumentProcessingStatus | None = None) -> None:
        super().__init__()
        self._icon = QLabel()
        self._text = QLabel()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(9, 3, 10, 3)
        layout.setSpacing(6)
        layout.addWidget(self._icon)
        layout.addWidget(self._text)

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("statusChip")

        if status is not None:
            self.set_status(status)

    def set_status(self, status: DocumentProcessingStatus) -> None:
        look = STATUS_LOOKS[status]
        swatch = look.swatch

        self._icon.setPixmap(icon_pixmap(look.icon, swatch.color, 12, 3.0))
        self._text.setText(look.label)
        self._text.setStyleSheet(
            f"color: {swatch.color}; font-size: 12px; font-weight: 500; background: transparent;"
        )
        self.setStyleSheet(f"QWidget#statusChip {{ background: {swatch.tint}; border-radius: 12px; }}")


def type_badge(file_type: str) -> QLabel:
    """Small colored badge such as PDF, MD or TXT."""

    swatch = t.file_type_swatch(file_type)

    widget = label(swatch.label, "badge")
    widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
    widget.setStyleSheet(f"background: {swatch.tint}; color: {swatch.color};")
    return widget
