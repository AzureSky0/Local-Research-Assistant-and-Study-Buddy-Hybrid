import os
from pathlib import Path

from platformdirs import user_data_dir

from app.core.constants import (
    APP_DATA_DIRECTORY_NAME,
    CACHE_DIRECTORY,
    CHROMA_DIRECTORY,
    DATABASE_DIRECTORY,
    DATA_DIR_ENV_VAR,
    DOCUMENT_DIRECTORY,
    LOG_DIRECTORY,
    MODEL_DIRECTORY,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

MIGRATIONS_DIR = PROJECT_ROOT / "app" / "database" / "migrations"
ALEMBIC_CONFIG_PATH = PROJECT_ROOT / "alembic.ini"


def _resolve_data_dir() -> Path:
    """Return the application data directory.

    Uses the per-user application data directory unless overridden
    by the LRA_DATA_DIR environment variable.
    """
    override = os.environ.get(DATA_DIR_ENV_VAR)

    if override:
        return Path(override).resolve()

    return Path(user_data_dir(APP_DATA_DIRECTORY_NAME, appauthor=False))


DATA_DIR = _resolve_data_dir()

DATABASE_DIR = DATA_DIR / DATABASE_DIRECTORY
DOCUMENTS_DIR = DATA_DIR / DOCUMENT_DIRECTORY
CHROMA_DIR = DATA_DIR / CHROMA_DIRECTORY
CACHE_DIR = DATA_DIR / CACHE_DIRECTORY
LOG_DIR = DATA_DIR / LOG_DIRECTORY
MODELS_DIR = DATA_DIR / MODEL_DIRECTORY

REQUIRED_DIRECTORIES = [
    DATA_DIR,
    DATABASE_DIR,
    DOCUMENTS_DIR,
    CHROMA_DIR,
    CACHE_DIR,
    LOG_DIR,
    MODELS_DIR,
]


def ensure_app_directories() -> None:
    """Create the application data directories if they do not exist."""
    for directory in REQUIRED_DIRECTORIES:
        directory.mkdir(parents=True, exist_ok=True)
