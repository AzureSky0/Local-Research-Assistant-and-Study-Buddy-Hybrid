from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.core.constants import APP_NAME
from app.ui.dialogs.workspace_dialog import WorkspaceDialog
from app.ui.formatting import format_relative_time, plural
from app.ui.managers.workspace_manager import WorkspaceManager
from app.ui.theme import mono_font
from app.ui.theme import tokens as t
from app.ui.theme.icons import icon
from app.ui.widgets.common import SearchField, button, hbox, icon_tile, label, surface, vbox
from app.workspace.domain.workspace import Workspace

CARD_MIN_WIDTH = 300
CARD_HEIGHT = 150


class WorkspaceCard(QPushButton):
    """A clickable workspace summary. Right-click or ⋯ for more actions."""

    menu_requested = Signal(str, QPoint)

    def __init__(self, workspace: Workspace, document_count: int, archived: bool) -> None:
        super().__init__()
        self.workspace = workspace
        self.setProperty("variant", "workspaceCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(CARD_HEIGHT)
        self.setAccessibleName(f"Open workspace {workspace.name}")

        swatch = t.workspace_swatch(workspace.color)

        name = label(workspace.name, "heading")
        description = label(workspace.description or "No description", "small")
        name.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        description.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        more = QPushButton()
        more.setProperty("variant", "ghost")
        more.setIcon(icon("more", t.MUTED, 18, 2.5))
        more.setFixedSize(32, 32)
        more.setToolTip("More actions")
        more.setAccessibleName(f"More actions for {workspace.name}")
        more.clicked.connect(
            lambda: self.menu_requested.emit(
                workspace.id, more.mapToGlobal(QPoint(0, more.height()))
            )
        )

        count = label(str(document_count))
        count.setFont(mono_font(13))
        count.setStyleSheet("font-weight: 500;")
        count_text = label("document" if document_count == 1 else "documents", "small")

        opened_at = workspace.last_opened_at or workspace.created_at
        when = label(
            ("Archived" if archived else "Opened ") + ("" if archived else format_relative_time(opened_at)),
            "small",
        )

        tile = icon_tile("folder", swatch.color, swatch.tint)

        for widget in (tile, count, count_text, when):
            widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.addLayout(hbox(tile, vbox(name, description, spacing=2), 1, more, spacing=12))
        layout.addStretch(1)
        layout.addLayout(hbox(count, count_text, 1, when, spacing=4))
        layout.setContentsMargins(20, 18, 20, 18)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(
            lambda position: self.menu_requested.emit(workspace.id, self.mapToGlobal(position))
        )


class HomePage(QWidget):
    """Lists workspaces and creates new ones."""

    settings_requested = Signal()

    def __init__(self, workspaces: WorkspaceManager) -> None:
        super().__init__()
        self.setObjectName("page")
        self._workspaces = workspaces
        self._show_archived = False
        self._cards: list[QWidget] = []

        # Header bar ------------------------------------------------------
        header = surface("header")
        mark = icon_tile("book", "#FFFFFF", t.ACCENT, size=32, icon_size=18)
        app_name = label(APP_NAME)
        app_name.setStyleSheet("font-weight: 600; font-size: 16px;")
        settings = button("Settings", None, "settings", t.INK)
        settings.clicked.connect(self.settings_requested)
        header_layout = hbox(mark, app_name, 1, settings, spacing=12)
        header_layout.setContentsMargins(48, 16, 48, 16)
        header.setLayout(header_layout)

        # Title row -------------------------------------------------------
        self._title = label("Your workspaces", "hero")
        self._subtitle = label(
            "Each workspace keeps its own documents, so projects never mix.", "muted"
        )
        new_workspace = button("New workspace", "primary", "plus", "#FFFFFF")
        new_workspace.clicked.connect(self.create_workspace)

        # Toolbar -----------------------------------------------------------
        self._search = SearchField("Find a workspace")
        self._search.setFixedWidth(340)
        self._search.input.textChanged.connect(self._apply_filter)

        self._archived_toggle = button("", "link")
        self._archived_toggle.clicked.connect(self._toggle_archived)

        # Card grid -----------------------------------------------------------
        self._grid_host = QWidget()
        self._grid = QGridLayout(self._grid_host)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(20)

        self._empty_hint = label("", "muted")
        self._empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_hint.hide()

        content = QWidget()
        content.setObjectName("page")
        content.setMaximumWidth(1120)
        content_layout = vbox(
            hbox(vbox(self._title, self._subtitle, spacing=6), 1, new_workspace),
            hbox(self._search, 1, self._archived_toggle, spacing=16),
            self._grid_host,
            self._empty_hint,
            1,
            spacing=28,
        )
        content_layout.setContentsMargins(48, 40, 48, 56)
        content.setLayout(content_layout)

        centered = QWidget()
        centered.setObjectName("page")
        centered_layout = hbox(1, content, 1, spacing=0)
        # Let the content grow up to its maximum width.
        centered_layout.setStretch(1, 100)
        centered.setLayout(centered_layout)

        scroll = QScrollArea()
        scroll.setObjectName("page")
        scroll.setWidgetResizable(True)
        scroll.setWidget(centered)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(header)
        layout.addWidget(scroll, 1)

        workspaces.workspaces_changed.connect(self.refresh)
        self.refresh()

    # Data --------------------------------------------------------------------

    def refresh(self) -> None:
        archived = self._workspaces.list_archived_workspaces()
        active = self._workspaces.list_workspaces()
        counts = self._workspaces.document_counts()

        if self._show_archived and not archived:
            self._show_archived = False

        self._archived_toggle.setVisible(bool(archived) or self._show_archived)
        self._archived_toggle.setText(
            "Show active workspaces" if self._show_archived else f"Show archived ({len(archived)})"
        )
        self._title.setText("Archived workspaces" if self._show_archived else "Your workspaces")
        self._subtitle.setText(
            "Restore a workspace to work with it again."
            if self._show_archived
            else "Each workspace keeps its own documents, so projects never mix."
        )

        shown = archived if self._show_archived else active

        self._cards = [
            self._make_card(workspace, counts.get(workspace.id, 0))
            for workspace in shown
        ]

        if not self._show_archived:
            create = QPushButton(" Create a workspace")
            create.setProperty("variant", "createCard")
            create.setIcon(icon("plus", t.ACCENT, 20))
            create.setFixedHeight(CARD_HEIGHT)
            create.setCursor(Qt.CursorShape.PointingHandCursor)
            create.clicked.connect(self.create_workspace)
            self._cards.append(create)

        self._apply_filter()

    def _make_card(self, workspace: Workspace, count: int) -> WorkspaceCard:
        card = WorkspaceCard(workspace, count, archived=self._show_archived)

        if not self._show_archived:
            card.clicked.connect(lambda: self._workspaces.open_workspace(workspace.id))

        card.menu_requested.connect(self._show_card_menu)
        return card

    def _apply_filter(self) -> None:
        query = self._search.text().strip().casefold()

        visible = [
            card
            for card in self._cards
            if not isinstance(card, WorkspaceCard)
            or query in card.workspace.name.casefold()
        ]

        if query:
            visible = [card for card in visible if isinstance(card, WorkspaceCard)]

        self._layout_cards(visible)

        has_matches = any(isinstance(card, WorkspaceCard) for card in visible)
        self._empty_hint.setVisible(bool(query) and not has_matches)
        self._empty_hint.setText(f"No workspace matches “{self._search.text().strip()}”.")

    def _layout_cards(self, cards: list[QWidget]) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            widget = item.widget() if item is not None else None

            # Cards from an earlier refresh are no longer needed.
            if widget is not None and widget not in self._cards:
                widget.hide()
                widget.deleteLater()

        columns = self._column_count()

        # Add to the grid before showing: showing a widget that has no
        # parent yet would open it as a separate window.
        for index, card in enumerate(cards):
            self._grid.addWidget(card, index // columns, index % columns)
            card.show()

        for card in self._cards:
            if card not in cards:
                card.hide()

        for column in range(columns):
            self._grid.setColumnStretch(column, 1)

    def _column_count(self) -> int:
        available = max(self._grid_host.width(), CARD_MIN_WIDTH)
        return max(1, min(3, (available + 20) // (CARD_MIN_WIDTH + 20)))

    def resizeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().resizeEvent(event)
        self._apply_filter()

    # Actions -------------------------------------------------------------------

    def _toggle_archived(self) -> None:
        self._show_archived = not self._show_archived
        self.refresh()

    def create_workspace(self) -> None:
        dialog = WorkspaceDialog(self)

        if dialog.exec() == WorkspaceDialog.DialogCode.Accepted:
            data = dialog.form_data()
            workspace = self._workspaces.create_workspace(data.name, data.description, data.color)
            self._workspaces.open_workspace(workspace.id)

    def _show_card_menu(self, workspace_id: str, position: QPoint) -> None:
        workspace = self._workspaces.get_workspace(workspace_id)

        if workspace is None:
            return

        menu = QMenu(self)

        if workspace.is_archived:
            menu.addAction("Restore", lambda: self._workspaces.restore_workspace(workspace_id))
        else:
            menu.addAction("Open", lambda: self._workspaces.open_workspace(workspace_id))
            menu.addAction("Edit details…", lambda: self._edit(workspace))
            menu.addAction("Archive", lambda: self._workspaces.archive_workspace(workspace_id))

        menu.addSeparator()
        menu.addAction("Delete permanently…", lambda: self._confirm_delete(workspace))
        menu.exec(position)

    def _edit(self, workspace: Workspace) -> None:
        dialog = WorkspaceDialog(self, workspace)

        if dialog.exec() == WorkspaceDialog.DialogCode.Accepted:
            data = dialog.form_data()
            self._workspaces.update_workspace(workspace.id, data.name, data.description, data.color)

    def _confirm_delete(self, workspace: Workspace) -> None:
        count = self._workspaces.document_counts().get(workspace.id, 0)

        answer = QMessageBox.warning(
            self,
            "Delete workspace",
            f"Delete “{workspace.name}” and its {plural(count, 'document')} permanently?\n\n"
            "This can’t be undone. Your original files stay on your computer.",
            QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.Cancel,
        )

        if answer == QMessageBox.StandardButton.Yes:
            self._workspaces.delete_workspace(workspace.id)
