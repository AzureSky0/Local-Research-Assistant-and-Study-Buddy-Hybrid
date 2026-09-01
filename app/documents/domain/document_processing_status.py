from enum import StrEnum


class DocumentProcessingStatus(StrEnum):
    """Represents the processing lifecycle of a document."""

    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    CANCELLED = "cancelled"