from __future__ import annotations

from sqlalchemy.orm import Session

from app.database.transaction import commit
from app.documents.domain import Document
from app.documents.mapper.document_mapper import DocumentMapper
from app.documents.repository.document_repository import DocumentRepository


class DocumentService:
    """Provides business operations for documents."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._repository = DocumentRepository(session)

    def create_document(self, document: Document) -> Document:
        """Create and persist a document."""
        document_orm = DocumentMapper.to_orm(document)

        self._repository.add(document_orm)
        commit(self._session)

        return DocumentMapper.to_domain(
            document_orm
        )

    def find_by_checksum(
        self,
        workspace_id: str,
        checksum: str,
    ) -> Document | None:
        """Return the workspace document with the given checksum, if any."""
        document_orm = self._repository.get_by_checksum(
            workspace_id,
            checksum,
        )

        if document_orm is None:
            return None

        return DocumentMapper.to_domain(document_orm)

    def get_documents(self, workspace_id: str) -> list[Document]:
        """Return all documents in a workspace."""
        documents_orm = self._repository.list_by_workspace(
            workspace_id
        )

        return [
            DocumentMapper.to_domain(document_orm)
            for document_orm in documents_orm
        ]

    def get_document_counts(self) -> dict[str, int]:
        """Return the number of documents in each workspace."""
        return self._repository.count_by_workspace()

    def remove_document(self, document_id: str) -> bool:
        """Remove a document from its workspace.

        Only the application's record is removed. The user's original
        file is never modified or deleted (FR-DOC-006).
        """
        document_orm = self._repository.get_by_id(document_id)

        if document_orm is None:
            return False

        self._repository.delete(document_orm)
        commit(self._session)

        return True

    def find_by_name(
        self,
        workspace_id: str,
        text: str,
        limit: int = 20,
    ) -> list[Document]:
        """Return workspace documents whose file name contains the text."""
        return [
            DocumentMapper.to_domain(document_orm)
            for document_orm in self._repository.search_by_name(workspace_id, text, limit)
        ]
