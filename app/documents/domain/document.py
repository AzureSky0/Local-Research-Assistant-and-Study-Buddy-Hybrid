from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.documents.domain.document_processing_status import (
    DocumentProcessingStatus,
)


@dataclass(slots=True)
class Document:
    """Business representation of a document."""

    id: str
    workspace_id: str
    file_name: str
    original_path: str
    file_size: int
    checksum: str
    file_type: str
    imported_at: datetime
    processing_status: DocumentProcessingStatus