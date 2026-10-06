"""link documents to workspaces

Every document now belongs to a workspace (Decision 003), and
duplicate detection is scoped to a workspace (Decision 021).

Existing documents without a workspace are moved into a default
"My Workspace" so no data is lost.

Revision ID: 5f2c8e1a9b34
Revises: a0c0931da9c6
Create Date: 2026-10-06 16:00:00.000000

"""

from datetime import UTC, datetime
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.schema import SchemaItem


# revision identifiers, used by Alembic.
revision: str = "5f2c8e1a9b34"
down_revision: Union[str, Sequence[str], None] = "a0c0931da9c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DEFAULT_WORKSPACE_NAME = "My Workspace"

FOREIGN_KEY_NAME = "fk_documents_workspace_id_workspaces"
UNIQUE_CONSTRAINT_NAME = "uq_documents_workspace_checksum"


def _documents_table(*extra: SchemaItem) -> sa.Table:
    """Explicit documents table definition used as the batch source.

    Databases created by earlier versions may contain an unnamed
    UNIQUE(checksum) constraint that cannot be dropped by name.
    Rebuilding from an explicit definition removes it consistently.
    """
    return sa.Table(
        "documents",
        sa.MetaData(),
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("original_path", sa.String(length=1024), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("file_type", sa.String(length=20), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "processing_status",
            sa.Enum(
                "PENDING",
                "PROCESSING",
                "READY",
                "FAILED",
                "CANCELLED",
                name="documentprocessingstatus",
            ),
            nullable=False,
        ),
        *extra,
    )


def _assign_orphan_documents_to_default_workspace() -> None:
    """Create a default workspace for existing documents, if there are any."""

    connection = op.get_bind()

    orphan_count = connection.execute(
        sa.text("SELECT COUNT(*) FROM documents WHERE workspace_id IS NULL")
    ).scalar_one()

    if orphan_count == 0:
        return

    workspace_id = str(uuid4())
    now = datetime.now(UTC)

    connection.execute(
        sa.text(
            "INSERT INTO workspaces "
            "(id, name, description, icon, color, created_at, updated_at, "
            "last_opened_at, is_archived) "
            "VALUES (:id, :name, NULL, 'folder', 'blue', :now, :now, NULL, 0)"
        ),
        {"id": workspace_id, "name": DEFAULT_WORKSPACE_NAME, "now": now},
    )

    connection.execute(
        sa.text("UPDATE documents SET workspace_id = :id WHERE workspace_id IS NULL"),
        {"id": workspace_id},
    )


def upgrade() -> None:
    """Upgrade schema."""

    # Step 1: rebuild the table without the global checksum uniqueness
    # and add a nullable workspace_id column.
    with op.batch_alter_table(
        "documents",
        copy_from=_documents_table(),
        recreate="always",
    ) as batch_op:
        batch_op.add_column(
            sa.Column("workspace_id", sa.String(length=36), nullable=True)
        )

    # Step 2: give existing documents a workspace.
    _assign_orphan_documents_to_default_workspace()

    # Step 3: make the link required and enforce per-workspace uniqueness.
    with op.batch_alter_table(
        "documents",
        copy_from=_documents_table(
            sa.Column("workspace_id", sa.String(length=36), nullable=True),
        ),
        recreate="always",
    ) as batch_op:
        batch_op.alter_column(
            "workspace_id",
            existing_type=sa.String(length=36),
            nullable=False,
        )
        batch_op.create_foreign_key(
            FOREIGN_KEY_NAME,
            "workspaces",
            ["workspace_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_unique_constraint(
            UNIQUE_CONSTRAINT_NAME,
            ["workspace_id", "checksum"],
        )


def downgrade() -> None:
    """Downgrade schema.

    Fails if the same file was imported into more than one workspace,
    because the previous schema required globally unique checksums.
    The default workspace created during upgrade is kept.
    """

    with op.batch_alter_table(
        "documents",
        copy_from=_documents_table(
            sa.Column(
                "workspace_id",
                sa.String(length=36),
                sa.ForeignKey(
                    "workspaces.id",
                    name=FOREIGN_KEY_NAME,
                    ondelete="CASCADE",
                ),
                nullable=False,
            ),
            sa.UniqueConstraint(
                "workspace_id",
                "checksum",
                name=UNIQUE_CONSTRAINT_NAME,
            ),
        ),
        recreate="always",
    ) as batch_op:
        batch_op.drop_constraint(UNIQUE_CONSTRAINT_NAME, type_="unique")
        batch_op.drop_constraint(FOREIGN_KEY_NAME, type_="foreignkey")
        batch_op.drop_column("workspace_id")

    op.create_index(
        op.f("ix_documents_checksum"),
        "documents",
        ["checksum"],
        unique=True,
    )
