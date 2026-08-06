from uuid import UUID

from app.models.document import Document
from app.documents.orm.document_orm import DocumentEntity


class DocumentMapper:

    @staticmethod
    def to_entity(
        document: Document,
    ) -> DocumentEntity:

        return DocumentEntity(
            id=str(document.id),
            file_name=document.file_name,
            original_path=str(document.original_path),
            file_size=document.file_size,
            checksum=document.checksum,
            file_type=document.file_type,
            imported_at=document.imported_at,
        )

    @staticmethod
    def to_model(
        entity: DocumentEntity,
    ) -> Document:

        return Document(
            id=UUID(entity.id),
            file_name=entity.file_name,
            original_path=entity.original_path,
            file_size=entity.file_size,
            checksum=entity.checksum,
            file_type=entity.file_type,
            imported_at=entity.imported_at,
        )