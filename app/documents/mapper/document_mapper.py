from __future__ import annotations

from app.documents.domain import Document
from app.documents.orm import DocumentORM


class DocumentMapper:
    """Converts between Document domain models and DocumentORM entities."""

    @staticmethod
    def to_orm(document: Document) -> DocumentORM:
        return DocumentORM(
            id=document.id,
            workspace_id=document.workspace_id,
            file_name=document.file_name,
            original_path=document.original_path,
            file_size=document.file_size,
            checksum=document.checksum,
            file_type=document.file_type,
            imported_at=document.imported_at,
            processing_status=document.processing_status,
            processed_stage=document.processed_stage,
            processing_error=document.processing_error,
            page_count=document.page_count,
            extractor_version=document.extractor_version,
        )

    @staticmethod
    def to_domain(document_orm: DocumentORM) -> Document:
        return Document(
            id=document_orm.id,
            workspace_id=document_orm.workspace_id,
            file_name=document_orm.file_name,
            original_path=document_orm.original_path,
            file_size=document_orm.file_size,
            checksum=document_orm.checksum,
            file_type=document_orm.file_type,
            imported_at=document_orm.imported_at,
            processing_status=document_orm.processing_status,
            processed_stage=document_orm.processed_stage,
            processing_error=document_orm.processing_error,
            page_count=document_orm.page_count,
            extractor_version=document_orm.extractor_version,
        )