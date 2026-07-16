from sqlalchemy import create_engine

from app.core.paths import DATABASE_DIR
from app.core.constants import DATABASE_FILENAME

DATABASE_PATH = DATABASE_DIR / DATABASE_FILENAME

DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
)
