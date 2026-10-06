from logging.config import fileConfig

from alembic import context

from app.core.paths import ensure_app_directories
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
from app.knowledge.orm.keyword_index_schema import is_keyword_index_table

# Future imports
# from app.knowledge.orm.knowledge_pack_orm import KnowledgePackORM
# from app.study.orm.flashcard_orm import FlashcardORM

config = context.config

# When migrations run from inside the application, the application's
# logging configuration is kept (see app.database.init_db).
if config.config_file_name is not None and config.attributes.get("configure_logging", True):
    fileConfig(config.config_file_name, disable_existing_loggers=False)

ensure_app_directories()

target_metadata = Base.metadata


def include_name(name: str | None, type_: str, parent_names: object) -> bool:
    """Skip schema objects that are managed by hand-written SQL.

    The FTS5 keyword index (a virtual table and its shadow tables)
    cannot be expressed as ORM models.
    """
    if type_ == "table":
        return not is_keyword_index_table(name)

    return True


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""

    context.configure(
        url=str(engine.url),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,
        include_name=include_name,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode."""

    with engine.connect() as connection:
        # Batch migrations rebuild tables (copy, drop, rename). With foreign
        # keys enforced, dropping the old table would cascade-delete child
        # rows, so enforcement is off while migrating and integrity is
        # checked afterwards.
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=True,
            include_name=include_name,
        )

        with context.begin_transaction():
            context.run_migrations()

        violations = connection.exec_driver_sql("PRAGMA foreign_key_check").fetchall()

        if violations:
            raise RuntimeError(
                f"Migration left {len(violations)} broken foreign key reference(s): "
                f"{violations[:5]}"
            )


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()