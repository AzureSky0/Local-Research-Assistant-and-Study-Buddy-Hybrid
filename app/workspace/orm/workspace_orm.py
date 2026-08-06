from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class WorkspaceORM(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    name : Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    description : Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    icon: Mapped[str] = mapped_column(
    String(50),
    nullable=False,
    default="folder",
    )

    color: Mapped[str] = mapped_column(
    String(30),
    nullable=False,
    default="blue",
    )

    created_at: Mapped[datetime] = mapped_column(
    DateTime,
    nullable=False,
    default=lambda: datetime.now(UTC)
    )

    updated_at: Mapped[datetime] = mapped_column(
    DateTime,
    nullable=False,
    default=lambda: datetime.now(UTC),
    onupdate=lambda: datetime.now(UTC),
    )

    last_opened_at: Mapped[datetime | None] = mapped_column(
    DateTime,
    nullable=True,
    )

    is_archived: Mapped[bool] = mapped_column(
    Boolean,
    nullable=False,
    default=False,
    )
    
