from __future__ import annotations

from uuid import uuid4

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ChunkORM(Base):
    """A retrievable passage of a document (Knowledge subsystem, PRD §84).

    Chunks are what embeddings and AI context are built from; the page
    range lets answers cite their source (PRD §85).
    """

    __tablename__ = "chunks"

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_chunks_document_index",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "documents.id",
            name="fk_chunks_document_id_documents",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # Position of the chunk within its document, from 0.
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    start_page: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    end_page: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    word_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Chunking settings used, so chunks can be rebuilt when they change.
    chunker_version: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    # Embedding model whose vector for this chunk is stored, or None when
    # it has not been embedded yet (or was embedded by another model).
    embedded_with: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )
