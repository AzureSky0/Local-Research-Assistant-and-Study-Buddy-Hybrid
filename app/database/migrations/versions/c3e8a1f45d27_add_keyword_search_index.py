"""add keyword search index

Creates the SQLite FTS5 keyword index over document pages and a
trigger that removes deleted documents from it (Knowledge subsystem).
Adds the "keyword_indexed" processing stage; documents that were
already read are indexed automatically on the next start.

The DDL is copied from app/knowledge/orm/keyword_index_schema.py as
it was when this migration was written; migrations must not change
when application code changes later.

Revision ID: c3e8a1f45d27
Revises: b7d41c2e9f10
Create Date: 2026-10-06 19:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3e8a1f45d27"
down_revision: Union[str, Sequence[str], None] = "b7d41c2e9f10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


OLD_STAGES = sa.Enum("REGISTERED", "EXTRACTED", name="documentprocessingstage")
NEW_STAGES = sa.Enum(
    "REGISTERED",
    "EXTRACTED",
    "KEYWORD_INDEXED",
    name="documentprocessingstage",
)


def upgrade() -> None:
    """Upgrade schema."""

    with op.batch_alter_table("documents") as batch_op:
        batch_op.alter_column(
            "processed_stage",
            existing_type=OLD_STAGES,
            type_=NEW_STAGES,
            existing_nullable=False,
        )

    op.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS page_search USING fts5(
            text,
            document_id UNINDEXED,
            page_number UNINDEXED,
            tokenize = 'porter unicode61 remove_diacritics 2'
        )
        """
    )

    op.execute(
        """
        CREATE TRIGGER IF NOT EXISTS documents_delete_from_page_search
        AFTER DELETE ON documents
        BEGIN
            DELETE FROM page_search WHERE document_id = old.id;
        END
        """
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.execute("DROP TRIGGER IF EXISTS documents_delete_from_page_search")
    op.execute("DROP TABLE IF EXISTS page_search")

    # Documents that reached the removed stage go back one stage.
    op.execute(
        "UPDATE documents SET processed_stage = 'EXTRACTED' "
        "WHERE processed_stage = 'KEYWORD_INDEXED'"
    )

    with op.batch_alter_table("documents") as batch_op:
        batch_op.alter_column(
            "processed_stage",
            existing_type=NEW_STAGES,
            type_=OLD_STAGES,
            existing_nullable=False,
        )
