from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QStackedWidget, QWidget

from app.ui.managers.activity_manager import ActivityManager, ImportActivity
from app.documents.domain import Document, DocumentProcessingStatus
from app.ui.managers.embedding_manager import EmbeddingManager
from app.ui.managers.library_manager import LibraryManager
from app.ui.managers.processing_manager import ProcessingManager
from app.ui.managers.workspace_manager import WorkspaceManager
from app.ui.pages.activity_page import ActivityPage
from app.ui.pages.library_page import LibraryPage
from app.ui.widgets.common import hbox
from app.ui.widgets.sidebar import ACTIVITY, LIBRARY, Sidebar
from app.workspace.domain.workspace import Workspace


class WorkspaceView(QWidget):
    """Everything inside an open workspace: sidebar, Library and Activity."""

    settings_requested = Signal()
    notification = Signal(str)

    def __init__(
        self,
        workspaces: WorkspaceManager,
        library: LibraryManager,
        activity: ActivityManager,
        processing: ProcessingManager,
        embedding: EmbeddingManager,
    ) -> None:
        super().__init__()
        self.setObjectName("page")
        self._embedding = embedding
        self._workspaces = workspaces
        self._library = library
        self._activity = activity

        self.sidebar = Sidebar(workspaces)
        self.library_page = LibraryPage(library, embedding)
        self.activity_page = ActivityPage(activity)

        self._pages = QStackedWidget()
        self._pages.addWidget(self.library_page)
        self._pages.addWidget(self.activity_page)

        layout = hbox(self.sidebar, self._pages, spacing=0)
        layout.setStretchFactor(self._pages, 1)
        self.setLayout(layout)

        self.sidebar.home_requested.connect(workspaces.close_workspace)
        self.sidebar.settings_requested.connect(self.settings_requested)
        self.sidebar.section_selected.connect(self.show_section)

        self.library_page.import_files_requested.connect(self._import_files)
        self.library_page.import_folder_requested.connect(self._import_folder)
        self.library_page.activity_requested.connect(lambda: self.show_section(ACTIVITY))
        self.activity_page.open_library_requested.connect(self._open_library)

        library.documents_reset.connect(lambda documents: self.sidebar.set_document_count(len(documents)))
        library.document_added.connect(lambda _: self._refresh_count())
        library.document_removed.connect(lambda _: self._refresh_count())
        activity.document_imported.connect(library.on_document_imported)

        # Reading starts as soon as the first document is imported.
        activity.document_imported.connect(lambda _: processing.start())
        processing.document_updated.connect(library.on_document_updated)

        processing.document_updated.connect(self._on_document_processed)
        self.library_page.retry_requested.connect(processing.retry)
        self.library_page.notification.connect(self.notification)
        activity.running_count_changed.connect(self._on_running_count_changed)

    def _on_document_processed(self, document: Document) -> None:
        # A document that finished reading has new passages to embed.
        if document.processing_status is DocumentProcessingStatus.READY:
            self._embedding.start()

    def show_workspace(self, workspace: Workspace) -> None:
        self.sidebar.set_workspace(workspace)
        self._library.load_workspace(workspace.id)
        self._on_running_count_changed(self._activity.running_count)
        self.show_section(LIBRARY)

    def show_section(self, key: str) -> None:
        self.sidebar.select(key)
        self._pages.setCurrentWidget(
            self.library_page if key == LIBRARY else self.activity_page
        )

    def _open_library(self, workspace_id: str) -> None:
        current = self._workspaces.current_workspace

        if current is None or current.id != workspace_id:
            self._workspaces.open_workspace(workspace_id)
        else:
            self.show_section(LIBRARY)

    def _import_files(self, files: list[Path]) -> ImportActivity | None:
        workspace = self._workspaces.current_workspace
        if workspace is None:
            return None

        return self._activity.import_files(workspace.id, workspace.name, files)

    def _import_folder(self, folder: Path) -> ImportActivity | None:
        workspace = self._workspaces.current_workspace
        if workspace is None:
            return None

        return self._activity.import_folder(workspace.id, workspace.name, folder)

    def _on_running_count_changed(self, count: int) -> None:
        self.sidebar.set_running_imports(count)
        self.library_page.set_running_imports(count)

    def _refresh_count(self) -> None:
        workspace = self._workspaces.current_workspace
        if workspace is not None:
            counts = self._workspaces.document_counts()
            self.sidebar.set_document_count(counts.get(workspace.id, 0))
