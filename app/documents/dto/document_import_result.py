from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.documents.domain import Document


class DocumentImportStatus(str, Enum):
    """Possible outcomes for an imported document."""

    IMPORTED = "imported"
    ALREADY_IMPORTED = "already_imported"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"


@dataclass(slots=True)
class DocumentImportResult:
    """Result of attempting to import one document."""

    file_path: str
    status: DocumentImportStatus
    document: Document | None = None
    error: str | None = None