import logging
import sys

from PySide6.QtWidgets import QApplication

from app.core.config import settings
from app.core.logging_setup import configure_logging
from app.core.paths import DATA_DIR, ensure_app_directories
from app.database.init_db import initialize_database
from app.ui.windows.main_window import MainWindow

logger = logging.getLogger(__name__)


def main() -> None:
    ensure_app_directories()
    configure_logging(debug=settings.debug)

    logger.info("Starting %s %s", settings.app_name, settings.app_version)
    logger.info("Data directory: %s", DATA_DIR)

    initialize_database()

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
