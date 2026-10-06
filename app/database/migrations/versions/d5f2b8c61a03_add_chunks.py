"""add chunks

Adds the chunks table (Knowledge subsystem) and the "chunked"
processing stage; documents that were already read are chunked
automatically on the next start.

Changing the stage column rebuilds the documents table, which drops its
triggers, so the keyword-index trigger is created again here.

Revision ID: d5f2b8c61a03
Revises: c3e8a1f45d27
Create Date: 2026-10-07 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d5f2b8c61a03"
down_revision: Union[str, Sequence[str], None] = "c3e8a1f45d27"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


OLD_STAGES = sa.Enum("REGISTERED", "EXTRACTED", "KEYWORD_INDEXED", name="documentprocessingstage")
NEW_STAGES = sa.Enum(
    "REGISTERED",
    "EXTRACTED",
    "KEYWORD_INDEXED",
    "CHUNKED",
    name="documentprocessingstage",
)

KEYWORD_INDEX_TRIGGER = """
    CREATE TRIGGER IF NOT EXISTS documents_delete_from_page_search
    AFTER DELETE ON documents
    BEGIN
        DELETE FROM page_search WHERE document_id = old.id;
    END
"""


def upgrade() -> None:
    """Upgrade schema."""

    with op.batch_alter_table("documents") as batch_op:
        batch_op.alter_column(
            "processed_stage",
            existing_type=OLD_STAGES,
            type_=NEW_STAGES,
            existing_nullable=False,
        )

    op.execute(KEYWORD_INDEX_TRIGGER)

    op.create_table(
        "chunks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("start_page", sa.Integer(), nullable=False),
        sa.Column("end_page", sa.Integer(), nullable=False),
        sa.Column("word_count", sa.Integer(), nullable=False),
        sa.Column("chunker_version", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name="fk_chunks_document_id_documents",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_chunks_document_index"),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table("chunks")

    op.execute(
        "UPDATE documents SET processed_stage = 'KEYWORD_INDEXED' "
        "WHERE processed_stage = 'CHUNKED'"
    )

    with op.batch_alter_table("documents") as batch_op:
        batch_op.alter_column(
            "processed_stage",
            existing_type=NEW_STAGES,
            type_=OLD_STAGES,
            existing_nullable=False,
        )

    op.execute(KEYWORD_INDEX_TRIGGER)
