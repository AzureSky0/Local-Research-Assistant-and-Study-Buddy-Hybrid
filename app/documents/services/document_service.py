from __future__ import annotations

from sqlalchemy.orm import Session

from app.documents.domain import Document
from app.documents.mapper.document_mapper import DocumentMapper
from app.documents.repository.document_repository import DocumentRepository


class DocumentService:
    """Provides business operations for documents."""

    def __init__(self, session: Session) -> None:
        self._repository = DocumentRepository(session)

    def create_document(self, document: Document) -> Document:
        """Create and persist a document."""
        document_orm = DocumentMapper.to_orm(document)

        saved_document = self._repository.create(
            document_orm
        )

        return DocumentMapper.to_domain(
            saved_document
        )

    def get_all_documents(self) -> list[Document]:
        """Return all documents."""
        documents_orm = self._repository.get_all()

        return [
            DocumentMapper.to_domain(document_orm)
            for document_orm in documents_orm
        ]