from alembic import command
from alembic.config import Config
from sqlalchemy import text

from app.core.paths import ALEMBIC_CONFIG_PATH, MIGRATIONS_DIR
from app.database.engine import engine
from app.knowledge.orm.keyword_index_schema import KEYWORD_INDEX_DDL


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

    command.upgrade(config, "head")

    ensure_keyword_index()


def ensure_keyword_index() -> None:
    """Re-create the keyword index and its trigger if they are missing.

    Rebuilding the documents table in a future migration silently drops
    its triggers, so this check runs on every start. The statements use
    IF NOT EXISTS and do nothing when everything is in place.
    """
    with engine.begin() as connection:
        for statement in KEYWORD_INDEX_DDL:
            connection.execute(text(statement))
