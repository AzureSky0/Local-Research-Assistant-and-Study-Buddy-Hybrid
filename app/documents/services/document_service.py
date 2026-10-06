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
