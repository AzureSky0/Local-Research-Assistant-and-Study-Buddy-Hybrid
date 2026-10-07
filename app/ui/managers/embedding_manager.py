from __future__ import annotations

import logging
import threading
from collections.abc import Callable

from PySide6.QtCore import QObject, Signal
from sqlalchemy.orm import Session

from app.core.computer_profile import ComputerProfile
from app.core.paths import MODELS_DIR
from app.core.tasks.async_task_executor import AsyncTaskExecutor
from app.core.tasks.task_handle import TaskHandle
from app.core.tasks.task_progress import TaskProgress
from app.core.tasks.task_result import TaskResult
from app.core.tasks.task_status import TaskStatus
from app.core.user_preferences import UserPreferences, load_preferences, save_preferences
from app.database.session import create_session
from app.knowledge.embeddings.embedder import (
    Embedder,
    EmbeddingModelUnavailableError,
    FastEmbedEmbedder,
)
from app.knowledge.embeddings.embedding_models import EmbeddingModelSpec, model_for_profile
from app.knowledge.services.embedding_service import EmbeddingService
from app.knowledge.tasks.embed_chunks_task import EmbedChunksTask

logger = logging.getLogger(__name__)

SessionFactory = Callable[[], Session]
EmbedderFactory = Callable[[EmbeddingModelSpec], Embedder]


def default_embedder_factory(spec: EmbeddingModelSpec) -> Embedder:
    return FastEmbedEmbedder(spec, MODELS_DIR)


class EmbeddingManager(QObject):
    """Keeps search by meaning up to date in the background (Decision 035).

    Embeds new chunks on its own worker, follows the computer profile
    (Decision 037), and offers a query embedder for searches once the
    model is loaded, so searching never waits for a model to load.
    """

    progress_changed = Signal(int, int)  # passages embedded, all passages
    unavailable = Signal(str)  # user-facing reason; word search still works
    profile_changed = Signal(object)  # ComputerProfile

    # Emitted from worker threads; delivered on the UI thread.
    _progress_reported = Signal(object)  # TaskProgress
    _run_finished = Signal(object)  # TaskResult
    _query_model_ready = Signal()

    def __init__(
        self,
        executor: AsyncTaskExecutor,
        session_factory: SessionFactory = create_session,
        embedder_factory: EmbedderFactory = default_embedder_factory,
        preferences: UserPreferences | None = None,
        save: Callable[[UserPreferences], None] = save_preferences,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._executor = executor
        self._session_factory = session_factory
        self._embedder_factory = embedder_factory
        self._preferences = preferences or load_preferences()
        self._save = save
        self._handle: TaskHandle | None = None
        self._more_work = False
        self._stopping = False
        self._unavailable_message: str | None = None

        self._progress_reported.connect(self._on_progress)
        self._run_finished.connect(self._on_run_finished)
        self._query_model_ready.connect(lambda: logger.info("Search model ready for queries"))

        self._create_embedders()

    # State -------------------------------------------------------------------------

    @property
    def profile(self) -> ComputerProfile:
        return self._preferences.effective_profile

    @property
    def is_automatic(self) -> bool:
        return self._preferences.is_automatic

    @property
    def spec(self) -> EmbeddingModelSpec:
        return self._worker_embedder.spec

    @property
    def unavailable_message(self) -> str | None:
        return self._unavailable_message

    @property
    def is_running(self) -> bool:
        return self._handle is not None

    def query_embedder(self) -> Embedder | None:
        """The embedder for search queries, or None until its model is loaded."""
        return self._query_embedder if self._query_ready.is_set() else None

    def progress(self, workspace_id: str | None = None) -> tuple[int, int]:
        with self._session_factory() as session:
            return EmbeddingService(session, self._worker_embedder).progress(workspace_id)

    # Commands --------------------------------------------------------------------------

    def start(self) -> None:
        """Embed any passages that are not embedded yet."""
        if self._stopping:
            return

        if self._handle is not None:
            self._more_work = True
            return

        self._handle = self._executor.submit(
            EmbedChunksTask(self._worker_embedder, self._session_factory),
            progress_callback=self._progress_reported.emit,
        )
        self._handle.add_done_callback(self._run_finished.emit)

    def set_profile(self, profile: ComputerProfile | None) -> None:
        """Choose a profile (None = automatic). Rebuilds the index if the model changes."""
        previous = self.spec
        self._preferences.computer_profile = profile.value if profile else None
        self._save(self._preferences)

        if model_for_profile(self.profile) != previous:
            if self._handle is not None:
                self._handle.cancel()
                self._more_work = True  # restart with the new model when the run stops
            self._create_embedders()
            if self._handle is None:
                self.start()

        self.profile_changed.emit(self.profile)

    def shutdown(self) -> None:
        self._stopping = True

        if self._handle is not None:
            self._handle.cancel()

        self._executor.shutdown()

    # Internals ------------------------------------------------------------------------------

    def _create_embedders(self) -> None:
        spec = model_for_profile(self.profile)
        self._worker_embedder = self._embedder_factory(spec)
        self._query_embedder = self._embedder_factory(spec)
        self._query_ready = threading.Event()
        self._unavailable_message = None
        self._preload_query_model()

    def _preload_query_model(self) -> None:
        """Load the query model off the UI thread, so a search never waits for it."""
        query_embedder, ready = self._query_embedder, self._query_ready

        def preload() -> None:
            try:
                query_embedder.load_model()
                ready.set()
                self._query_model_ready.emit()
            except EmbeddingModelUnavailableError:
                pass  # reported by the embedding run

        threading.Thread(target=preload, name="search-model-preload", daemon=True).start()

    def _on_progress(self, progress: TaskProgress) -> None:
        self.progress_changed.emit(progress.current, progress.total)

    def _on_run_finished(self, result: TaskResult) -> None:
        self._handle = None

        if result.status is TaskStatus.FAILED:
            if isinstance(result.error, EmbeddingModelUnavailableError):
                self._unavailable_message = str(result.error)
                self.unavailable.emit(self._unavailable_message)
                return
            logger.error("Embedding run failed: %s", result.error)

        if self._stopping:
            return

        # The model may have been downloaded by this run (e.g. back online).
        if result.status is TaskStatus.COMPLETED and not self._query_ready.is_set():
            self._unavailable_message = None
            self._preload_query_model()

        if self._more_work:
            self._more_work = False
            self.start()
