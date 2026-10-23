from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import text

from app.core.paths import ALEMBIC_CONFIG_PATH, DATABASE_DIR, MIGRATIONS_DIR
from app.database.backup import backup_database
from app.database.engine import DATABASE_PATH, engine
from app.knowledge.orm.keyword_index_schema import KEYWORD_INDEX_DDL

BACKUP_DIR = DATABASE_DIR / "backups"


def initialize_database() -> None:
    """Bring the database schema up to date by running Alembic migrations.

    Safe to call on every start-up: Alembic only applies migrations
    that have not been applied yet, and creates the database on first run.
    """
    config = Config(str(ALEMBIC_CONFIG_PATH))
    config.set_main_option("script_location", str(MIGRATIONS_DIR))

    # Keep the application's logging configuration instead of
    # letting env.py load the logging setup from alembic.ini.
    config.attributes["configure_logging"] = False

    backup_if_upgrading(config)
    command.upgrade(config, "head")

    ensure_keyword_index()


def backup_if_upgrading(config: Config) -> None:
    """Copy the database before migrations change an existing library.

    Nothing is copied on the first start (no library yet) or when the
    schema is already up to date.
    """
    if not DATABASE_PATH.exists():
        return

    with engine.connect() as connection:
        current = MigrationContext.configure(connection).get_current_revision()

    heads = ScriptDirectory.from_config(config).get_heads()
    if current is None or current in heads:
        return

    backup_database(DATABASE_PATH, BACKUP_DIR, label=current)


def ensure_keyword_index() -> None:
    """Re-create the keyword index and its trigger if they are missing.

    Rebuilding the documents table in a future migration silently drops
    its triggers, so this check runs on every start. The statements use
    IF NOT EXISTS and do nothing when everything is in place.
    """
    with engine.begin() as connection:
        for statement in KEYWORD_INDEX_DDL:
            connection.execute(text(statement))
