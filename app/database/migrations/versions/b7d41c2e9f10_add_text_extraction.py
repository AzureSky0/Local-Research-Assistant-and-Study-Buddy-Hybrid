"""add text extraction

Adds staged processing columns to documents (Decision 031) and the
document_pages table holding extracted text per page.

Existing documents start at the "registered" stage, so they are read
automatically the next time the application starts.

Revision ID: b7d41c2e9f10
Revises: 5f2c8e1a9b34
Create Date: 2026-10-06 18:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7d41c2e9f10"
down_revision: Union[str, Sequence[str], None] = "5f2c8e1a9b34"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PROCESSING_STAGE = sa.Enum(
    "REGISTERED",
    "EXTRACTED",
    name="documentprocessingstage",
)


def upgrade() -> None:
    """Upgrade schema."""

    with op.batch_alter_table("documents") as batch_op:
        batch_op.add_column(
            sa.Column(
                "processed_stage",
                PROCESSING_STAGE,
                nullable=False,
                server_default="REGISTERED",
            )
        )
        batch_op.add_column(sa.Column("processing_error", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("page_count", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("extractor_version", sa.String(length=64), nullable=True))

    # The default only existed to fill existing rows.
    with op.batch_alter_table("documents") as batch_op:
        batch_op.alter_column(
            "processed_stage",
            existing_type=PROCESSING_STAGE,
            server_default=None,
        )

    # Documents left "processing" by an older version are read again.
    op.execute(
        "UPDATE documents SET processing_status = 'PENDING' "
        "WHERE processing_status = 'PROCESSING'"
    )

    op.create_table(
        "document_pages",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name="fk_document_pages_document_id_documents",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id",
            "page_number",
            name="uq_document_pages_document_page",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table("document_pages")

    with op.batch_alter_table("documents") as batch_op:
        batch_op.drop_column("extractor_version")
        batch_op.drop_column("page_count")
        batch_op.drop_column("processing_error")
        batch_op.drop_column("processed_stage")
