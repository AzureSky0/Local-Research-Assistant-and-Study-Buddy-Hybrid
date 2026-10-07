from __future__ import annotations

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QMainWindow, QMessageBox, QStackedWidget

from app.core.constants import APP_NAME
from app.documents.dto.document_import_result import DocumentImportStatus
from app.ui.formatting import plural
from app.ui.managers.activity_manager import ActivityManager, ActivityState, ImportActivity
from app.ui.managers.background_manager import BackgroundManager
from app.ui.managers.embedding_manager import EmbeddingManager
from app.ui.managers.library_manager import LibraryManager
from app.ui.managers.processing_manager import ProcessingManager
from app.ui.managers.workspace_manager import WorkspaceManager
from app.ui.pages.home_page import HomePage
from app.ui.pages.settings_page import SettingsPage
from app.ui.theme import tokens as t
from app.ui.widgets.status_pill import StatusPanel, StatusPill
from app.ui.widgets.toast import Toast
from app.ui.windows.workspace_view import WorkspaceView
from app.workspace.domain.workspace import Workspace


class MainWindow(QMainWindow):
    """Top-level window: workspaces home, an open workspace, or settings."""

    def __init__(
        self,
        workspaces: WorkspaceManager,
        library: LibraryManager,
        activity: ActivityManager,
        processing: ProcessingManager,
        embedding: EmbeddingManager,
        background: BackgroundManager | None = None,
    ) -> None:
        super().__init__()
        self._workspaces = workspaces
        self._activity = activity

        self.setWindowTitle(APP_NAME)
        self.resize(1280, 820)
        self.setMinimumSize(960, 640)

        self.home_page = HomePage(workspaces)
        self.workspace_view = WorkspaceView(workspaces, library, activity, processing, embedding)
        self.settings_page = SettingsPage(embedding)

        self._stack = QStackedWidget()
        self._stack.setObjectName("appRoot")
        self._stack.addWidget(self.home_page)
        self._stack.addWidget(self.workspace_view)
        self._stack.addWidget(self.settings_page)
        self.setCentralWidget(self._stack)

        self.toast = Toast(self._stack)

        # Background work and computer health, bottom right (Decision 033).
        self.status_pill = StatusPill(self._stack)
        self.status_panel = StatusPanel(self, embedding.profile)
        self.toast.bottom_offset = 16 + 32 + 12  # above the pill

        if background is not None:
            background.status_changed.connect(self.status_pill.show_status)
            background.status_changed.connect(self.status_panel.show_status)
            self.status_pill.clicked.connect(lambda: self.status_panel.show_above(self.status_pill))
            self.status_panel.pause_requested.connect(background.pause)
            self.status_panel.resume_requested.connect(background.resume)
        else:
            self.status_pill.hide()

        self.home_page.settings_requested.connect(self._show_settings)
        self.workspace_view.settings_requested.connect(self._show_settings)
        self.workspace_view.notification.connect(
            lambda message: self.toast.show_message(
                message, icon_name="file", icon_color=t.TOAST_LINK
            )
        )
        self.settings_page.back_requested.connect(self._show_current)
        workspaces.current_workspace_changed.connect(self._on_workspace_changed)
        activity.activity_finished.connect(self._on_import_finished)

    def _on_workspace_changed(self, workspace: Workspace | None) -> None:
        if workspace is None:
            self.setWindowTitle(APP_NAME)
            self._stack.setCurrentWidget(self.home_page)
            return

        self.setWindowTitle(f"{workspace.name} — {APP_NAME}")
        self.workspace_view.show_workspace(workspace)
        self._stack.setCurrentWidget(self.workspace_view)

    def _show_settings(self) -> None:
        self._stack.setCurrentWidget(self.settings_page)

    def _show_current(self) -> None:
        if self._workspaces.current_workspace is None:
            self._stack.setCurrentWidget(self.home_page)
        else:
            self._stack.setCurrentWidget(self.workspace_view)

    def _on_import_finished(self, activity: ImportActivity) -> None:
        added = activity.count(DocumentImportStatus.IMPORTED)
        problems = activity.count(DocumentImportStatus.FAILED) + activity.count(
            DocumentImportStatus.UNSUPPORTED
        )

        if activity.state is ActivityState.FAILED:
            message = f"An import into {activity.workspace_name} stopped because of an error."
            icon_name, color = "alert", "#F5B38A"
        else:
            message = f"{plural(added, 'file')} added to {activity.workspace_name}"
            if problems:
                message += f" · {plural(problems, 'file')} need attention"
            icon_name, color = ("alert", "#F5B38A") if problems else ("check", t.TOAST_SUCCESS)

        self.toast.show_message(
            message,
            "View",
            lambda: self._view_activity(activity),
            icon_name=icon_name,
            icon_color=color,
        )

    def _view_activity(self, activity: ImportActivity) -> None:
        current = self._workspaces.current_workspace

        if current is None or current.id != activity.workspace_id:
            self._workspaces.open_workspace(activity.workspace_id)

        self.workspace_view.show_section("activity")
        self._stack.setCurrentWidget(self.workspace_view)

    def closeEvent(self, event: QCloseEvent) -> None:
        running = self._activity.running_count

        if running:
            answer = QMessageBox.question(
                self,
                "Imports still running",
                f"{plural(running, 'import')} still running. Stop and quit?\n\n"
                "Files added so far are kept.",
                QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes,
                QMessageBox.StandardButton.Cancel,
            )

            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return

        event.accept()
