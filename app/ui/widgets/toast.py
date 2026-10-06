from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QEvent, QObject, QTimer, Qt
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QPushButton, QWidget
from PySide6.QtGui import QColor

from app.ui.theme import tokens as t
from app.ui.theme.icons import icon_pixmap

DISPLAY_MILLISECONDS = 6000
MARGIN = 28


class Toast(QWidget):
    """A short notification shown in the bottom-right corner of a window."""

    def __init__(self, host: QWidget) -> None:
        super().__init__(host)
        self.setObjectName("toast")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedWidth(380)

        self._icon = QLabel()
        self._icon.setPixmap(icon_pixmap("check", t.TOAST_SUCCESS, 20, 2.5))

        self._message = QLabel()
        self._message.setWordWrap(True)

        self._action = QPushButton()
        self._action.setCursor(Qt.CursorShape.PointingHandCursor)
        self._action.clicked.connect(self._run_action)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 14, 14)
        layout.setSpacing(12)
        layout.addWidget(self._icon)
        layout.addWidget(self._message, 1)
        layout.addWidget(self._action)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(32)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(20, 24, 33, 80))
        self.setGraphicsEffect(shadow)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

        self._callback: Callable[[], None] | None = None

        host.installEventFilter(self)
        self.hide()

    def show_message(
        self,
        message: str,
        action_text: str | None = None,
        on_action: Callable[[], None] | None = None,
        icon_name: str = "check",
        icon_color: str = t.TOAST_SUCCESS,
    ) -> None:
        self._icon.setPixmap(icon_pixmap(icon_name, icon_color, 20, 2.5))
        self._message.setText(message)
        self._callback = on_action

        self._action.setVisible(action_text is not None)
        self._action.setText(action_text or "")

        self.adjustSize()
        self._reposition()
        self.show()
        self.raise_()
        self._timer.start(DISPLAY_MILLISECONDS)

    def _run_action(self) -> None:
        self.hide()

        if self._callback is not None:
            self._callback()

    def _reposition(self) -> None:
        host = self.parentWidget()

        if host is not None:
            self.move(
                host.width() - self.width() - MARGIN,
                host.height() - self.height() - MARGIN,
            )

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Resize and self.isVisible():
            self._reposition()

        return super().eventFilter(watched, event)
