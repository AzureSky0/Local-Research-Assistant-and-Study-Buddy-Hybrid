from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.models.enums import ImportStatus, IndexStatus


class Document(BaseModel):
    id: UUID = Field(default_factory=uuid4)

    file_name: str
    original_path: Path

    imported_at: datetime = Field(default_factory=datetime.utcnow)

    file_size: int
    checksum: str
    file_type: str

    page_count: int | None = None

    title: str | None = None
    author: str | None = None
    subject: str | None = None
    keywords: list[str] = Field(default_factory=list)
    language: str | None = None

    import_status: ImportStatus = ImportStatus.PENDING
    index_status: IndexStatus = IndexStatus.NOT_STARTED

    chunk_count: int = 0
    embedding_count: int = 0

    last_processed_at: datetime | None = None