from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.documents.domain import DocumentProcessingStatus

from app.database.base import Base
from app.database.types import UTCDateTime


class DocumentORM(Base):
    """
    SQLAlchemy ORM model representing an imported document.
    """

    __tablename__ = "documents"

    __table_args__ = (
        # The same file may be imported into different workspaces,
        # but only once per workspace (Decision 021).
        UniqueConstraint(
            "workspace_id",
            "checksum",
            name="uq_documents_workspace_checksum",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "workspaces.id",
            name="fk_documents_workspace_id_workspaces",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    original_path: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    checksum: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    file_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    imported_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    processing_status: Mapped[DocumentProcessingStatus] = mapped_column(
        Enum(DocumentProcessingStatus),
        nullable=False,
        default=DocumentProcessingStatus.PENDING,
    )
