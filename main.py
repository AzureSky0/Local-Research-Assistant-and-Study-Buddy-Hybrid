import logging
import os
import sys
from types import TracebackType

from PySide6.QtWidgets import QApplication

from app.core.config import settings
from app.core.logging_setup import configure_logging
from app.core.paths import DATA_DIR, ensure_app_directories
from app.core.tasks.async_task_executor import AsyncTaskExecutor
from app.database.init_db import initialize_database
from app.ui.managers.activity_manager import ActivityManager
from app.ui.managers.background_manager import BackgroundManager
from app.ui.managers.embedding_manager import EmbeddingManager
from app.ui.managers.library_manager import LibraryManager
from app.ui.managers.processing_manager import ProcessingManager
from app.ui.managers.workspace_manager import WorkspaceManager
from app.ui.theme import apply_theme
from app.ui.windows.main_window import MainWindow

logger = logging.getLogger(__name__)

# Imports are mostly disk-bound; two workers keep the UI responsive
# while letting a second import start without waiting.
IMPORT_WORKERS = 2


def log_unhandled_error(
    error_type: type[BaseException], error: BaseException, traceback: TracebackType | None
) -> None:
    """Write crashes to the log file: the packaged app has no console to show them."""
    logger.critical("Unexpected error", exc_info=(error_type, error, traceback))


def provide_missing_console_streams() -> None:
    """The packaged app has no console, so sys.stdout and sys.stderr are None.

    Libraries that print (for example the model download's progress bar)
    would then crash; send their output nowhere instead.
    """
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")


def main() -> None:
    provide_missing_console_streams()
    ensure_app_directories()
    configure_logging(debug=settings.debug)
    sys.excepthook = log_unhandled_error

    logger.info("Starting %s %s", settings.app_name, settings.app_version)
    logger.info("Data directory: %s", DATA_DIR)

    initialize_database()

    app = QApplication(sys.argv)
    app.setApplicationName(settings.app_name)
    apply_theme(app)

    # Search by meaning: embeds passages on its own worker (Decision 035).
    embedding = EmbeddingManager(AsyncTaskExecutor(max_workers=1))
    logger.info("Computer profile: %s, search model: %s", embedding.profile.label, embedding.spec.model_id)

    workspaces = WorkspaceManager()
    library = LibraryManager(query_embedder=embedding.query_embedder)
    activity = ActivityManager(AsyncTaskExecutor(max_workers=IMPORT_WORKERS))

    # Reading documents has its own single worker, separate from imports.
    processing = ProcessingManager(AsyncTaskExecutor(max_workers=1))

    # Stop background work cleanly when the application exits.
    app.aboutToQuit.connect(activity.shutdown)
    app.aboutToQuit.connect(processing.shutdown)
    app.aboutToQuit.connect(embedding.shutdown)

    # Watches the computer and pauses background work when memory runs low.
    background = BackgroundManager(activity, processing, embedding)
    app.aboutToQuit.connect(background.stop)

    window = MainWindow(workspaces, library, activity, processing, embedding, background)
    window.show()

    # Resume anything left unfinished last time.
    processing.recover_and_start()
    embedding.start()
    background.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
