from logging.config import fileConfig

from alembic import context

from app.database.base import Base
from app.database.engine import engine

# -------------------------------------------------------------------------
# Import ALL ORM models here.
#
# The imports are intentionally unused.
# Importing them registers their tables with SQLAlchemy's metadata so
# Alembic can detect schema changes.
# -------------------------------------------------------------------------

from app.documents.orm import DocumentORM  # noqa: F401
from app.workspace.orm import WorkspaceORM  # noqa: F401

# Future imports
# from app.knowledge.orm.knowledge_pack_orm import KnowledgePackORM
# from app.study.orm.flashcard_orm import FlashcardORM

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""

    context.configure(
        url=str(engine.url),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode."""

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()