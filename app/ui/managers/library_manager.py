from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject, Signal
from sqlalchemy.orm import Session

from app.database.session import create_session
from app.documents.domain import Document
from app.documents.services.document_service import DocumentService

SessionFactory = Callable[[], Session]


class LibraryManager(QObject):
    """Holds the documents of the current workspace for the Library page."""

    documents_reset = Signal(list)  # list[Document]
    document_added = Signal(object)  # Document
    document_removed = Signal(str)  # document id
    document_updated = Signal(object)  # Document

    def __init__(
        self,
        session_factory: SessionFactory = create_session,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._session_factory = session_factory
        self._workspace_id: str | None = None

    @property
    def workspace_id(self) -> str | None:
        return self._workspace_id

    def load_workspace(self, workspace_id: str | None) -> None:
        """Load the documents of a workspace (None clears the library)."""
        self._workspace_id = workspace_id

        if workspace_id is None:
            self.documents_reset.emit([])
            return

        with self._session_factory() as session:
            documents = DocumentService(session).get_documents(workspace_id)

        self.documents_reset.emit(documents)

    def on_document_imported(self, document: Document) -> None:
        """Show a newly imported document if it belongs to the open workspace."""
        if document.workspace_id == self._workspace_id:
            self.document_added.emit(document)

    def on_document_updated(self, document: Document) -> None:
        """Refresh a document whose processing status changed."""
        if document.workspace_id == self._workspace_id:
            self.document_updated.emit(document)

    def remove_document(self, document_id: str) -> bool:
        """Remove a document from the workspace. The original file is untouched."""
        with self._session_factory() as session:
            removed = DocumentService(session).remove_document(document_id)

        if removed:
            self.document_removed.emit(document_id)

        return removed
