from alembic import command
from alembic.config import Config

from app.core.paths import ALEMBIC_CONFIG_PATH, MIGRATIONS_DIR


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
