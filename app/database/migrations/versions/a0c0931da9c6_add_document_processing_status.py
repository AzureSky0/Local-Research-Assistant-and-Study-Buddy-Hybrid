"""add document processing status

Revision ID: a0c0931da9c6
Revises: 8668c557c8bf
Create Date: 2026-08-27 16:22:45.273794

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a0c0931da9c6"
down_revision: Union[str, Sequence[str], None] = "8668c557c8bf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    with op.batch_alter_table("documents") as batch_op:
        batch_op.add_column(
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
                server_default="PENDING",
            )
        )

    with op.batch_alter_table("documents") as batch_op:
        batch_op.alter_column(
            "processing_status",
            server_default=None,
        )


def downgrade() -> None:
    """Downgrade schema."""

    with op.batch_alter_table("documents") as batch_op:
        batch_op.drop_column("processing_status")