import logging
import sys

from PySide6.QtWidgets import QApplication

from app.core.config import settings
from app.core.logging_setup import configure_logging
from app.core.paths import DATA_DIR, ensure_app_directories
from app.core.tasks.async_task_executor import AsyncTaskExecutor
from app.database.init_db import initialize_database
from app.ui.managers.activity_manager import ActivityManager
from app.ui.managers.library_manager import LibraryManager
from app.ui.managers.workspace_manager import WorkspaceManager
from app.ui.theme import apply_theme
from app.ui.windows.main_window import MainWindow

logger = logging.getLogger(__name__)

# Imports are mostly disk-bound; two workers keep the UI responsive
# while letting a second import start without waiting.
IMPORT_WORKERS = 2


def main() -> None:
    ensure_app_directories()
    configure_logging(debug=settings.debug)

    logger.info("Starting %s %s", settings.app_name, settings.app_version)
    logger.info("Data directory: %s", DATA_DIR)

    initialize_database()

    app = QApplication(sys.argv)
    app.setApplicationName("Study Buddy")
    apply_theme(app)

    workspaces = WorkspaceManager()
    library = LibraryManager()
    activity = ActivityManager(AsyncTaskExecutor(max_workers=IMPORT_WORKERS))

    # Stop background imports cleanly when the application exits.
    app.aboutToQuit.connect(activity.shutdown)

    window = MainWindow(workspaces, library, activity)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
