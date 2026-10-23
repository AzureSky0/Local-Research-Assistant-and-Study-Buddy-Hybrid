import logging
import os
import sys
from types import TracebackType

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMessageBox, QSplashScreen

from app.core.config import settings
from app.core.logging_setup import configure_logging
from app.core.constants import LOG_FILENAME
from app.core.paths import DATA_DIR, LOG_DIR, ensure_app_directories
from app.core.single_instance import SingleInstance
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


def make_splash() -> QSplashScreen:
    """A small window shown at once, so a slow first start is not mistaken for a failure."""
    pixmap = QPixmap(420, 160)
    pixmap.fill(QColor("#FFFFFF"))
    painter = QPainter(pixmap)
    painter.fillRect(0, 0, 420, 6, QColor("#2F4FCB"))
    painter.setPen(QColor("#16181D"))
    painter.setFont(QFont("Segoe UI", 20, QFont.Weight.DemiBold))
    painter.drawText(32, 72, settings.app_name)
    painter.setPen(QColor("#5B6170"))
    painter.setFont(QFont("Segoe UI", 11))
    painter.drawText(32, 108, "Starting… the first start can take a minute.")
    painter.end()
    splash = QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)
    return splash


def show_startup_failure() -> None:
    QMessageBox.critical(
        None,
        f"{settings.app_name} could not start",
        f"Something went wrong while starting {settings.app_name}.\n\n"
        f"Details are in the log file:\n{LOG_DIR / LOG_FILENAME}\n\n"
        "Please try again. If it keeps happening, send the log file to the developer.",
    )


def main() -> int:
    provide_missing_console_streams()
    ensure_app_directories()
    configure_logging(debug=settings.debug)
    sys.excepthook = log_unhandled_error

    app = QApplication(sys.argv)
    app.setApplicationName(settings.app_name)

    # One copy per data folder: a second start brings the first window forward.
    instance = SingleInstance(DATA_DIR)
    if not instance.acquire():
        logger.info("%s is already running; asking it to show its window", settings.app_name)
        if not instance.ask_running_copy_to_show():
            QMessageBox.information(None, settings.app_name, f"{settings.app_name} is already open.")
        return 0

    splash = make_splash()
    splash.show()
    app.processEvents()

    try:
        logger.info("Starting %s %s", settings.app_name, settings.app_version)
        logger.info("Data directory: %s", DATA_DIR)

        initialize_database()
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
        app.aboutToQuit.connect(instance.release)

        # Watches the computer and pauses background work when memory runs low.
        background = BackgroundManager(activity, processing, embedding)
        app.aboutToQuit.connect(background.stop)

        window = MainWindow(workspaces, library, activity, processing, embedding, background)
        instance.activation_requested.connect(lambda: bring_to_front(window))
        window.show()
        splash.finish(window)

        # Resume anything left unfinished last time.
        processing.recover_and_start()
        embedding.start()
        background.start()
    except Exception:
        logger.exception("Could not start")
        splash.close()
        show_startup_failure()
        instance.release()
        return 1

    return app.exec()


def bring_to_front(window: MainWindow) -> None:
    if window.isMinimized():
        window.showNormal()
    window.show()
    window.raise_()
    window.activateWindow()


if __name__ == "__main__":
    sys.exit(main())
