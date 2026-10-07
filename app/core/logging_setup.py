import logging
from logging.handlers import RotatingFileHandler

from app.core.constants import LOG_FILENAME
from app.core.paths import LOG_DIR

LOG_FORMAT = "%(asctime)s %(levelname)-8s [%(name)s] %(message)s"

MAX_LOG_BYTES = 1_000_000
LOG_BACKUP_COUNT = 3


def configure_logging(debug: bool = False) -> None:
    """Configure application logging.

    Logs are written to a rotating file in the application log
    directory, and to the console when debug mode is enabled.
    """
    formatter = logging.Formatter(LOG_FORMAT)

    file_handler = RotatingFileHandler(
        LOG_DIR / LOG_FILENAME,
        maxBytes=MAX_LOG_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    handlers: list[logging.Handler] = [file_handler]

    if debug:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)

    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        handlers=handlers,
        force=True,
    )

    # SQLAlchemy is very verbose at DEBUG level, and the model download
    # logs every web request.
    for noisy in ("sqlalchemy", "httpx", "httpcore", "huggingface_hub"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
