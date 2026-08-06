from pathlib import Path

from app.database.session import get_session
from app.documents.mapper.document_mapper import DocumentMapper
from app.models.document import Document
from app.documents.repository.document_repository import DocumentRepository


class DocumentService:

    def __init__(self):
        self.session = get_session()
        self.repository = DocumentRepository(
            self.session
        )

    def create_document(
        self,
        document: Document,
    ) -> Document:

        entity = DocumentMapper.to_entity(
            document
        )

        saved_entity = self.repository.create(
            entity
        )

        return DocumentMapper.to_model(
            saved_entity
        )

    def get_all_documents(
        self,
    ) -> list[Document]:

        entities = self.repository.get_all()

        return [
            DocumentMapper.to_model(entity)
            for entity in entities
        ]