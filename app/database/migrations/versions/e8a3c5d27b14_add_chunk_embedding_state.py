"""add chunk embedding state

Records which embedding model produced each chunk's vector, so search
by meaning can resume after a restart and rebuild when the model
changes. The vector tables themselves (sqlite-vec) are created at run
time, one per model.

Adding a column does not rebuild the chunks table, so its triggers are
kept.

Revision ID: e8a3c5d27b14
Revises: d5f2b8c61a03
Create Date: 2026-10-07 16:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e8a3c5d27b14"
down_revision: Union[str, Sequence[str], None] = "d5f2b8c61a03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column("chunks", sa.Column("embedded_with", sa.String(length=128), nullable=True))
    op.create_index(op.f("ix_chunks_embedded_with"), "chunks", ["embedded_with"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(op.f("ix_chunks_embedded_with"), table_name="chunks")

    with op.batch_alter_table("chunks") as batch_op:
        batch_op.drop_column("embedded_with")
