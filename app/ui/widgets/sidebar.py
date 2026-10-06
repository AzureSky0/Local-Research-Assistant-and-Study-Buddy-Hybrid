from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QSizePolicy,
    QFrame,
    QLabel,
    QMenu,
    QPushButton,
    QToolButton,
    QVBoxLayout,
)

from app.ui.managers.workspace_manager import WorkspaceManager
from app.ui.theme import mono_font
from app.ui.theme import tokens as t
from app.ui.theme.icons import icon
from app.ui.widgets.common import clear_layout, button, hbox, icon_label, icon_tile, label, vbox
from app.workspace.domain.workspace import Workspace

LIBRARY = "library"
ACTIVITY = "activity"


class Sidebar(QFrame):
    """Navigation inside a workspace."""

    home_requested = Signal()
    settings_requested = Signal()
    section_selected = Signal(str)  # LIBRARY | ACTIVITY

    def __init__(self, workspaces: WorkspaceManager) -> None:
        super().__init__()
        self.setProperty("surface", "sidebar")
        self.setFixedWidth(250)
        self._workspaces = workspaces

        back = button("All workspaces", "ghost", "chevron-left", t.MUTED)
        back.clicked.connect(self.home_requested)

        # Workspace switcher ---------------------------------------------------
        self._switcher = QToolButton()
        self._switcher.setProperty("variant", "workspaceSwitcher")
        self._switcher.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._switcher.setCursor(Qt.CursorShape.PointingHandCursor)
        self._switcher.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._switcher_menu = QMenu(self._switcher)
        self._switcher_menu.aboutToShow.connect(self._fill_switcher_menu)
        self._switcher.setMenu(self._switcher_menu)

        self._tile_holder = QVBoxLayout()
        self._tile_holder.setContentsMargins(0, 0, 0, 0)
        self._workspace_name = label("")
        self._workspace_name.setStyleSheet("font-weight: 600; font-size: 14px;")
        switch_hint = label("Switch workspace", "small")
        switch_hint.setStyleSheet(f"font-size: 12px; color: {t.MUTED};")
        chevron = icon_label("chevron-down", t.MUTED, 16)

        switcher_layout = hbox(
            self._tile_holder,
            vbox(self._workspace_name, switch_hint, spacing=0),
            1,
            chevron,
            spacing=10,
        )
        switcher_layout.setContentsMargins(10, 8, 10, 8)
        self._switcher.setLayout(switcher_layout)
        self._switcher.setMinimumHeight(58)

        for child in (self._workspace_name, switch_hint, chevron):
            child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Navigation ----------------------------------------------------------
        self._nav = QButtonGroup(self)
        self._nav.setExclusive(True)

        self._library_button, self._library_count = self._nav_button("Library", "book", LIBRARY)
        self._activity_button, self._activity_badge = self._nav_button("Activity", "activity", ACTIVITY)
        self._activity_badge.setStyleSheet(
            f"background: {t.ACCENT}; color: #FFFFFF; border-radius: 10px; "
            "font-size: 12px; font-weight: 500; padding: 1px 7px;"
        )
        self._activity_badge.hide()

        settings = button("Settings", "nav", "settings", t.SUBTLE)
        settings.setIconSize(QSize(18, 18))
        settings.clicked.connect(self.settings_requested)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(20)
        layout.addWidget(back, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._switcher)
        layout.addLayout(vbox(self._library_button, spacing=4))
        layout.addStretch(1)
        layout.addLayout(vbox(self._activity_button, settings, spacing=4))

        self._library_button.setChecked(True)

    def _nav_button(self, text: str, icon_name: str, key: str) -> tuple[QPushButton, QLabel]:
        nav_button = button(text, "nav", icon_name, t.SUBTLE)
        nav_button.setCheckable(True)
        nav_button.setIconSize(QSize(18, 18))
        nav_button.clicked.connect(lambda: self.section_selected.emit(key))
        self._nav.addButton(nav_button)

        trailing = QLabel()
        trailing.setFont(mono_font(12))
        trailing.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        inner = hbox(1, trailing, spacing=0)
        inner.setContentsMargins(0, 0, 12, 0)
        nav_button.setLayout(inner)

        return nav_button, trailing

    # Updates ----------------------------------------------------------------

    def set_workspace(self, workspace: Workspace) -> None:
        swatch = t.workspace_swatch(workspace.color)

        clear_layout(self._tile_holder)

        tile = icon_tile("folder", swatch.color, swatch.tint, size=32, icon_size=16)
        tile.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._tile_holder.addWidget(tile)

        metrics = self._workspace_name.fontMetrics()
        self._workspace_name.setText(
            metrics.elidedText(workspace.name, Qt.TextElideMode.ElideRight, 140)
        )
        self._switcher.setToolTip(workspace.name)
        self._switcher.setAccessibleName(f"Current workspace: {workspace.name}. Switch workspace")

    def set_document_count(self, count: int) -> None:
        self._library_count.setText(str(count) if count else "")

    def set_running_imports(self, count: int) -> None:
        self._activity_badge.setText(str(count))
        self._activity_badge.setVisible(count > 0)

    def select(self, key: str) -> None:
        (self._library_button if key == LIBRARY else self._activity_button).setChecked(True)

    def _fill_switcher_menu(self) -> None:
        self._switcher_menu.clear()
        current = self._workspaces.current_workspace

        for workspace in self._workspaces.list_workspaces():
            swatch = t.workspace_swatch(workspace.color)
            action = self._switcher_menu.addAction(
                icon("folder", swatch.color, 16),
                workspace.name,
                lambda workspace_id=workspace.id: self._workspaces.open_workspace(workspace_id),
            )
            action.setCheckable(True)
            action.setChecked(current is not None and workspace.id == current.id)

        self._switcher_menu.addSeparator()
        self._switcher_menu.addAction(
            icon("chevron-left", t.MUTED, 16),
            "All workspaces",
            self.home_requested.emit,
        )
