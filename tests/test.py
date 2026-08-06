from pathlib import Path
from uuid import uuid4
from app.models.document import Document
from app.documents.services.document_service import (
    DocumentService,
)

service = DocumentService()

document = Document(
    file_name="example.pdf",
    original_path=Path(
        r"D:\Temp\example.pdf"
    ),
    file_size=1024,
    checksum=str(uuid4()),
    file_type="pdf",
)

saved = service.create_document(
    document
)

documents = service.get_all_documents()