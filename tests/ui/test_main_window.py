"""End-to-end UI tests: real widgets, real background imports, offscreen."""

from collections.abc import Callable, Generator
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication
from sqlalchemy.orm import Session

from app.core.tasks.async_task_executor import AsyncTaskExecutor
from app.documents.dto.document_import_result import DocumentImportStatus
from app.core.user_preferences import UserPreferences
from app.ui.managers.activity_manager import ActivityManager, ActivityState
from app.ui.managers.embedding_manager import EmbeddingManager
from app.ui.managers.library_manager import LibraryManager
from app.ui.managers.processing_manager import ProcessingManager
from app.ui.managers.workspace_manager import WorkspaceManager
from app.ui.pages.home_page import WorkspaceCard
from app.ui.windows.main_window import MainWindow
from tests.knowledge.fake_embedder import FakeEmbedder
from tests.ui.conftest import make_library, wait_until


@pytest.fixture
def window(
    qapp: QApplication,
    session_factory: Callable[[], Session],
) -> Generator[MainWindow, None, None]:
    embedding = EmbeddingManager(
        AsyncTaskExecutor(max_workers=1),
        session_factory,
        embedder_factory=lambda spec: FakeEmbedder(),
        preferences=UserPreferences(),
        save=lambda preferences: None,
    )
    workspaces = WorkspaceManager(session_factory)
    library = LibraryManager(session_factory, query_embedder=embedding.query_embedder)
    activity = ActivityManager(AsyncTaskExecutor(max_workers=1), session_factory)
    processing = ProcessingManager(AsyncTaskExecutor(max_workers=1), session_factory)

    main_window = MainWindow(workspaces, library, activity, processing, embedding)
    main_window.resize(1280, 800)
    main_window.show()

    yield main_window

    activity.shutdown()
    processing.shutdown()
    embedding.shutdown()
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


def test_imported_documents_are_read_and_become_ready(
    window: MainWindow,
    tmp_path: Path,
) -> None:
    import pymupdf

    from app.documents.domain import DocumentProcessingStatus

    folder = tmp_path / "papers"
    folder.mkdir()
    for name in ("attention.pdf", "adam.pdf"):
        document = pymupdf.open()
        document.new_page().insert_text((72, 72), f"Text of {name}")
        document.save(folder / name)
        document.close()
    (folder / "notes.md").write_text("# Gradient descent", encoding="utf-8")

    workspace = window._workspaces.create_workspace("Machine Learning", None, "blue")
    window._workspaces.open_workspace(workspace.id)
    window.workspace_view._import_folder(folder)

    model = window.workspace_view.library_page._model

    wait_until(
        lambda: len(model.documents) == 3
        and all(d.processing_status is DocumentProcessingStatus.READY for d in model.documents)
    )

    assert all(d.page_count == 1 for d in model.documents)


def test_scanned_pdf_shows_reason_and_can_be_retried(
    window: MainWindow,
    tmp_path: Path,
) -> None:
    import pymupdf

    from app.documents.domain import DocumentProcessingStatus

    path = tmp_path / "scan.pdf"
    document = pymupdf.open()
    document.new_page()  # a page without any text layer
    document.save(path)
    document.close()

    workspace = window._workspaces.create_workspace("Scans", None, "blue")
    window._workspaces.open_workspace(workspace.id)
    window.workspace_view._import_files([path])

    page = window.workspace_view.library_page
    wait_until(
        lambda: len(page._model.documents) == 1
        and page._model.documents[0].processing_status is DocumentProcessingStatus.FAILED
    )

    page._table.selectRow(0)
    wait_until(lambda: page._details.isVisible())
    assert page._details._problem.isVisibleTo(page._details)
    assert "OCR" in page._details._problem_text.text()

    # The user adds text (for example after running OCR elsewhere) and retries.
    document = pymupdf.open()
    document.new_page().insert_text((72, 72), "Now with text")
    document.save(path)
    document.close()

    page._details.retry_requested.emit(page._model.documents[0])

    wait_until(
        lambda: page._model.documents[0].processing_status is DocumentProcessingStatus.READY
    )
    assert not page._details._problem.isVisibleTo(page._details)


def test_search_finds_text_inside_documents(
    window: MainWindow,
    tmp_path: Path,
) -> None:
    import pymupdf

    from app.documents.domain import DocumentProcessingStatus

    folder = tmp_path / "papers"
    folder.mkdir()
    document = pymupdf.open()
    document.new_page().insert_text((72, 72), "Introduction")
    document.new_page().insert_text((72, 72), "Gradient descent with momentum")
    document.save(folder / "optimizers.pdf")
    document.close()
    (folder / "gradient-notes.md").write_text("# Unrelated title", encoding="utf-8")

    workspace = window._workspaces.create_workspace("Machine Learning", None, "blue")
    window._workspaces.open_workspace(workspace.id)
    window.workspace_view._import_folder(folder)

    page = window.workspace_view.library_page
    wait_until(
        lambda: len(page._model.documents) == 2
        and all(d.processing_status is DocumentProcessingStatus.READY for d in page._model.documents)
    )

    page._search.input.setText("gradient")
    wait_until(lambda: page._browse.currentIndex() == 1)

    results = page._results
    # Two sections (file names, inside documents) plus one row each.
    assert results.row_count == 4
    assert "1 document" in results._summary.text()

    passage_index = results._model.index(3, 0)
    results._list.clicked.emit(passage_index)
    assert page._details.document is not None
    assert page._details.document.file_name == "optimizers.pdf"

    page._search.input.clear()
    wait_until(lambda: page._browse.currentIndex() == 0)


def test_double_clicking_a_result_opens_it_at_that_page(
    window: MainWindow,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import pymupdf

    from app.documents.domain import DocumentProcessingStatus
    from app.ui.document_opener import OpenResult
    from app.ui.pages import library_page as library_page_module

    opened: list[tuple[Path, int | None]] = []

    def fake_open(path: Path, page: int | None = None) -> OpenResult:
        opened.append((path, page))
        return OpenResult(opened=True, at_page=True)

    monkeypatch.setattr(library_page_module, "open_document", fake_open)

    path = tmp_path / "book.pdf"
    document = pymupdf.open()
    for text in ["Contents", "Preface", "Backpropagation explained"]:
        document.new_page().insert_text((72, 72), text)
    document.save(path)
    document.close()

    workspace = window._workspaces.create_workspace("Books", None, "blue")
    window._workspaces.open_workspace(workspace.id)
    window.workspace_view._import_files([path])

    page = window.workspace_view.library_page
    wait_until(
        lambda: len(page._model.documents) == 1
        and page._model.documents[0].processing_status is DocumentProcessingStatus.READY
    )

    page._search.input.setText("backpropagation")
    wait_until(lambda: page._browse.currentIndex() == 1)

    results = page._results
    passage_row = results.row_count - 1
    results._list.activated.emit(results._model.index(passage_row, 0))

    assert opened == [(path, 3)]
    assert page._details._open.text() == "Open at page 3"


def test_details_panel_closes_with_button_and_escape(
    window: MainWindow,
    tmp_path: Path,
) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    (tmp_path / "notes.md").write_text("# Notes", encoding="utf-8")
    workspace = window._workspaces.create_workspace("Notes", None, "blue")
    window._workspaces.open_workspace(workspace.id)
    window.workspace_view._import_files([tmp_path / "notes.md"])

    page = window.workspace_view.library_page
    wait_until(lambda: len(page._model.documents) == 1)

    # Close button
    page._table.selectRow(0)
    wait_until(lambda: page._details.isVisible())
    page._details.close_requested.emit()
    assert not page._details.isVisible()
    assert not page._table.selectionModel().hasSelection()

    # Escape key
    page._table.selectRow(0)
    wait_until(lambda: page._details.isVisible())
    page._table.setFocus()
    QTest.keyClick(page._table, Qt.Key.Key_Escape)
    wait_until(lambda: not page._details.isVisible())
    assert not page._table.selectionModel().hasSelection()


def test_search_by_meaning_after_documents_are_embedded(
    window: MainWindow,
    tmp_path: Path,
) -> None:
    from app.documents.domain import DocumentProcessingStatus

    folder = tmp_path / "notes"
    folder.mkdir()
    (folder / "adam.md").write_text("Adam keeps moving averages of gradients.", encoding="utf-8")
    (folder / "cnn.md").write_text("Convolutional networks for images.", encoding="utf-8")

    workspace = window._workspaces.create_workspace("Notes", None, "blue")
    window._workspaces.open_workspace(workspace.id)
    window.workspace_view._import_folder(folder)

    page = window.workspace_view.library_page
    embedding = window.workspace_view._embedding
    wait_until(
        lambda: len(page._model.documents) == 2
        and all(d.processing_status is DocumentProcessingStatus.READY for d in page._model.documents)
    )
    wait_until(lambda: embedding.progress(workspace.id) == (2, 2) and not embedding.is_running)
    wait_until(lambda: embedding.query_embedder() is not None)

    # "optimiser" is not in the note; meaning connects it to Adam.
    page._search.input.setText("optimiser averages")
    wait_until(lambda: page._browse.currentIndex() == 1)

    assert "by words and meaning" in page._results._summary.text()
    assert page._results._model.item(1).text() == "adam.md"
    assert not page._meaning_row.isVisibleTo(page)



def test_home_shows_document_counts_after_import(window: MainWindow, tmp_path: Path) -> None:
    folder = tmp_path / "notes"
    folder.mkdir()
    for name in ("a.md", "b.md"):
        (folder / name).write_text(f"Notes in {name}.", encoding="utf-8")

    workspace = window._workspaces.create_workspace("Notes", None, "blue")
    window._workspaces.open_workspace(workspace.id)
    window.workspace_view._import_folder(folder)
    wait_until(lambda: len(window.workspace_view.library_page._model.documents) == 2)

    window._workspaces.close_workspace()

    card = next(c for c in window.home_page._cards if c.workspace.id == workspace.id)
    assert card.document_count == 2


def test_settings_scrolls_instead_of_squeezing_text(window: MainWindow) -> None:
    from PySide6.QtWidgets import QLabel

    window.resize(900, 400)
    window._show_settings()
    window.show()
    QApplication.processEvents()

    for text in window.settings_page.findChildren(QLabel):
        if text.isVisible() and text.wordWrap():
            assert text.height() >= text.heightForWidth(text.width()), text.text()
