from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.documents.domain import (
    Document,
    DocumentProcessingStatus,
)
from app.documents.services.document_service import DocumentService

def test_create_and_get_document(session: Session) -> None:
    service = DocumentService(session)

    document = Document(
        id="test-document-id",
        file_name="example.pdf",
        original_path=r"D:\Temp\example.pdf",
        file_size=1024,
        checksum="test-checksum",
        file_type="pdf",
        imported_at=datetime.now(UTC),
        processing_status=DocumentProcessingStatus.PENDING,
    )

    saved = service.create_document(document)

    assert saved.id == document.id
    assert saved.file_name == "example.pdf"
    assert saved.original_path == r"D:\Temp\example.pdf"
    assert saved.file_size == 1024
    assert saved.checksum == "test-checksum"
    assert saved.file_type == "pdf"

    documents = service.get_all_documents()

    assert len(documents) == 1
    assert documents[0].id == document.id
    