from datetime import datetime , UTC
from uuid import uuid4

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class DocumentORM(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    file_name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    original_path: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    checksum: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
    )

    file_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    imported_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )