import logging
import sys

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


def main() -> None:
    ensure_app_directories()
    configure_logging(debug=settings.debug)

    logger.info("Starting %s %s", settings.app_name, settings.app_version)
    logger.info("Data directory: %s", DATA_DIR)

    initialize_database()

    app = QApplication(sys.argv)
    app.setApplicationName("Study Buddy")
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
