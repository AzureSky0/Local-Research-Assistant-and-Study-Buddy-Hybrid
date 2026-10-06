"""End-to-end UI tests: real widgets, real background imports, offscreen."""

from collections.abc import Callable, Generator
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication
from sqlalchemy.orm import Session

from app.core.tasks.async_task_executor import AsyncTaskExecutor
from app.documents.dto.document_import_result import DocumentImportStatus
from app.ui.managers.activity_manager import ActivityManager, ActivityState
from app.ui.managers.library_manager import LibraryManager
from app.ui.managers.workspace_manager import WorkspaceManager
from app.ui.pages.home_page import WorkspaceCard
from app.ui.windows.main_window import MainWindow
from tests.ui.conftest import make_library, wait_until


@pytest.fixture
def window(
    qapp: QApplication,
    session_factory: Callable[[], Session],
) -> Generator[MainWindow, None, None]:
    workspaces = WorkspaceManager(session_factory)
    library = LibraryManager(session_factory)
    activity = ActivityManager(AsyncTaskExecutor(max_workers=1), session_factory)

    main_window = MainWindow(workspaces, library, activity)
    main_window.resize(1280, 800)
    main_window.show()

    yield main_window

    activity.shutdown()
    main_window.close()
    main_window.deleteLater()


def visible_cards(window: MainWindow) -> list[WorkspaceCard]:
    return [
        card
        for card in window.home_page._cards
        if isinstance(card, WorkspaceCard) and card.isVisible()
    ]


def test_home_lists_workspaces_and_filters_by_name(window: MainWindow) -> None:
    workspaces = window._workspaces
    workspaces.create_workspace("Machine Learning", "Papers", "blue")
    workspaces.create_workspace("German B1", None, "orange")

    wait_until(lambda: len(visible_cards(window)) == 2)

    window.home_page._search.input.setText("german")

    wait_until(lambda: len(visible_cards(window)) == 1)
    assert visible_cards(window)[0].workspace.name == "German B1"


def test_opening_a_workspace_shows_its_empty_library(window: MainWindow) -> None:
    workspace = window._workspaces.create_workspace("Thesis", None, "purple")

    window._workspaces.open_workspace(workspace.id)

    assert window._stack.currentWidget() is window.workspace_view
    library_page = window.workspace_view.library_page
    assert library_page._content.currentWidget() is library_page._empty


def test_folder_import_updates_library_and_activity(
    window: MainWindow,
    tmp_path: Path,
) -> None:
    folder = make_library(tmp_path / "library")
    workspace = window._workspaces.create_workspace("Machine Learning", None, "blue")
    window._workspaces.open_workspace(workspace.id)

    activity_manager = window._activity
    activity = window.workspace_view._import_folder(folder)
    assert activity is not None

    wait_until(lambda: not activity.is_running)

    assert activity.state is ActivityState.FINISHED
    assert activity.count(DocumentImportStatus.IMPORTED) == 3
    assert activity.count(DocumentImportStatus.UNSUPPORTED) == 1
    assert activity.count(DocumentImportStatus.FAILED) == 1
    assert activity_manager.running_count == 0

    # The Library shows the imported documents.
    library_page = window.workspace_view.library_page
    assert len(library_page._model.documents) == 3
    assert library_page._content.currentWidget() is not library_page._empty

    # The Activity page moved the card to "finished" and lists both problems.
    activity_page = window.workspace_view.activity_page
    assert activity_page._running_list.count() == 0
    assert activity_page._finished_list.count() == 1
    assert not activity_page._running_title.isVisibleTo(activity_page)

    card = activity_page._cards[activity.id]
    assert card._issues.count() == 2

    # A toast announces the result.
    assert window.toast.isVisible()


def test_removing_a_document_keeps_the_original_file(
    window: MainWindow,
    tmp_path: Path,
) -> None:
    folder = make_library(tmp_path / "library")
    workspace = window._workspaces.create_workspace("Machine Learning", None, "blue")
    window._workspaces.open_workspace(workspace.id)

    activity = window.workspace_view._import_folder(folder)
    assert activity is not None
    wait_until(lambda: not activity.is_running)

    library_page = window.workspace_view.library_page
    document = library_page._model.documents[0]

    assert library_page._library.remove_document(document.id) is True

    assert all(d.id != document.id for d in library_page._model.documents)
    assert Path(document.original_path).exists()


def test_cancelling_an_import_keeps_finished_files(
    window: MainWindow,
    tmp_path: Path,
) -> None:
    folder = tmp_path / "many"
    folder.mkdir()
    for index in range(200):
        (folder / f"note-{index:03}.md").write_text(f"# Note {index}", encoding="utf-8")

    workspace = window._workspaces.create_workspace("Notes", None, "teal")
    window._workspaces.open_workspace(workspace.id)

    activity = window.workspace_view._import_folder(folder)
    assert activity is not None

    window._activity.cancel(activity.id)
    wait_until(lambda: not activity.is_running)

    imported = activity.count(DocumentImportStatus.IMPORTED)
    assert activity.state is ActivityState.CANCELLED
    assert imported < 200
    assert len(window.workspace_view.library_page._model.documents) == imported
