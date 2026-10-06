from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QItemSelection, QModelIndex, Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QFileDialog,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableView,
    QWidget,
)

from app.documents.domain import Document
from app.documents.supported_formats import SUPPORTED_EXTENSIONS
from app.ui.formatting import plural
from app.ui.managers.library_manager import LibraryManager
from app.ui.models.document_table_delegate import DocumentTableDelegate
from app.ui.models.document_table_model import (
    ADDED_COLUMN,
    DOCUMENT_ROLE,
    FILTER_ALL,
    NAME_COLUMN,
    SIZE_COLUMN,
    STATUS_COLUMN,
    DocumentFilterProxyModel,
    DocumentTableModel,
)
from app.ui.theme import tokens as t
from app.ui.widgets.common import STATUS_LOOKS, SearchField, button, hbox, label, vbox
from app.ui.widgets.library.document_details_panel import DocumentDetailsPanel
from app.ui.widgets.library.empty_library_widget import EmptyLibraryWidget

FILE_DIALOG_FILTER = "Documents ({})".format(
    " ".join(f"*{extension}" for extension in SUPPORTED_EXTENSIONS)
)

STATUS_FILTERS = [
    (FILTER_ALL, "All"),
    ("ready", "Ready"),
    ("in_progress", "In progress"),
    ("attention", "Needs attention"),
]


class LibraryPage(QWidget):
    """The documents of the current workspace."""

    import_files_requested = Signal(list)  # list[Path]
    import_folder_requested = Signal(object)  # Path
    activity_requested = Signal()

    def __init__(self, library: LibraryManager) -> None:
        super().__init__()
        self.setObjectName("page")
        self.setAcceptDrops(True)
        self._library = library
        self._running_imports = 0

        # Header ------------------------------------------------------------
        title = label("Library", "title")
        self._summary = label("", "muted")
        self._activity_link = button("", "link")
        self._activity_link.clicked.connect(self.activity_requested)

        add_files = button("Add files", "primary", "plus", "#FFFFFF")
        add_files.clicked.connect(self.choose_files)
        add_folder = button("Add folder", "secondary", "folder", t.INK)
        add_folder.clicked.connect(self.choose_folder)

        header = hbox(
            vbox(title, hbox(self._summary, self._activity_link, 1, spacing=6), spacing=4),
            1,
            add_files,
            add_folder,
        )

        # Toolbar -------------------------------------------------------------
        self._search = SearchField("Search documents by name")

        self._filter_group = QButtonGroup(self)
        self._filter_group.setExclusive(True)
        self._filter_buttons: dict[str, QPushButton] = {}

        filters = hbox(spacing=6)
        for key, text in STATUS_FILTERS:
            filter_button = button(text, "filter")
            filter_button.setCheckable(True)
            filter_button.setChecked(key == FILTER_ALL)
            filter_button.setProperty("filterKey", key)
            filter_button.setProperty("baseText", text)
            self._filter_group.addButton(filter_button)
            self._filter_buttons[key] = filter_button
            filters.addWidget(filter_button)

        # Table ---------------------------------------------------------------
        self._model = DocumentTableModel()
        self._proxy = DocumentFilterProxyModel()
        self._proxy.setSourceModel(self._model)

        self._table = QTableView()
        self._table.setModel(self._proxy)
        self._table.setItemDelegate(DocumentTableDelegate(self._table))
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setShowGrid(False)
        self._table.setSortingEnabled(True)
        self._table.sortByColumn(ADDED_COLUMN, Qt.SortOrder.DescendingOrder)
        self._table.verticalHeader().hide()
        self._table.verticalHeader().setDefaultSectionSize(46)
        self._table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self._table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self._table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        horizontal = self._table.horizontalHeader()
        horizontal.setSectionResizeMode(NAME_COLUMN, QHeaderView.ResizeMode.Stretch)
        horizontal.setSectionResizeMode(STATUS_COLUMN, QHeaderView.ResizeMode.Fixed)
        horizontal.setSectionResizeMode(SIZE_COLUMN, QHeaderView.ResizeMode.Fixed)
        horizontal.setSectionResizeMode(ADDED_COLUMN, QHeaderView.ResizeMode.Fixed)
        horizontal.resizeSection(STATUS_COLUMN, 170)
        horizontal.resizeSection(SIZE_COLUMN, 100)
        horizontal.resizeSection(ADDED_COLUMN, 130)
        horizontal.setHighlightSections(False)

        self._no_matches = label("No documents match your search or filter.", "muted")
        self._no_matches.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._no_matches.hide()

        tip = label("Tip: drop files or folders anywhere in this window to add them.", "small")

        # Details panel ---------------------------------------------------------
        self._details = DocumentDetailsPanel()
        self._details.hide()
        self._details.remove_requested.connect(self._confirm_remove)

        # Assemble ----------------------------------------------------------------
        self._empty = EmptyLibraryWidget()
        self._empty.add_files_requested.connect(self.choose_files)
        self._empty.add_folder_requested.connect(self.choose_folder)

        list_view = QWidget()
        list_layout = vbox(
            self._search,
            hbox(filters, 1),
            self._table,
            self._no_matches,
            tip,
            spacing=16,
        )
        list_layout.setStretchFactor(self._table, 1)
        list_view.setLayout(list_layout)

        self._content = QStackedWidget()
        self._content.addWidget(self._empty)
        self._content.addWidget(list_view)

        main = QWidget()
        main_layout = vbox(header, self._content, spacing=24)
        main_layout.setStretchFactor(self._content, 1)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main.setLayout(main_layout)

        layout = hbox(main, self._details, spacing=0)
        layout.setStretchFactor(main, 1)
        self.setLayout(layout)

        # Signals ---------------------------------------------------------------
        self._search.input.textChanged.connect(self._on_filter_changed)
        self._filter_group.buttonClicked.connect(self._on_filter_changed)
        self._table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self._proxy.rowsInserted.connect(self._update_summary)
        self._proxy.modelReset.connect(self._update_summary)
        self._proxy.rowsRemoved.connect(self._update_summary)

        library.documents_reset.connect(self._on_documents_reset)
        library.document_added.connect(self._model.add_document)
        library.document_added.connect(lambda _: self._update_summary())
        library.document_removed.connect(self._on_document_removed)

        self._update_summary()

    # External updates ---------------------------------------------------------

    def set_running_imports(self, count: int) -> None:
        self._running_imports = count
        self._update_summary()

    # Adding documents ---------------------------------------------------------

    def choose_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Add files",
            str(Path.home()),
            FILE_DIALOG_FILTER,
        )

        if paths:
            self.import_files_requested.emit([Path(path) for path in paths])

    def choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Add a folder", str(Path.home()))

        if folder:
            self.import_folder_requested.emit(Path(folder))

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls() and any(url.isLocalFile() for url in event.mimeData().urls()):
            event.acceptProposedAction()
            self._empty.set_drag_active(True)

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self._empty.set_drag_active(False)

    def dropEvent(self, event: QDropEvent) -> None:
        self._empty.set_drag_active(False)

        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()]
        files = [path for path in paths if path.is_file()]
        folders = [path for path in paths if path.is_dir()]

        if files:
            self.import_files_requested.emit(files)

        for folder in folders:
            self.import_folder_requested.emit(folder)

        event.acceptProposedAction()

    # Internals ------------------------------------------------------------------

    def _on_documents_reset(self, documents: list[Document]) -> None:
        self._search.clear()
        self._filter_buttons[FILTER_ALL].setChecked(True)
        self._proxy.set_status_group(FILTER_ALL)
        self._model.set_documents(documents)
        self._details.show_document(None)

    def _on_document_removed(self, document_id: str) -> None:
        self._model.remove_document(document_id)
        self._details.show_document(None)

    def _on_filter_changed(self) -> None:
        checked = self._filter_group.checkedButton()
        group = str(checked.property("filterKey")) if checked else FILTER_ALL

        self._proxy.set_text(self._search.text())
        self._proxy.set_status_group(group)
        self._update_summary()

    def _on_selection_changed(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        indexes = self._table.selectionModel().selectedRows()
        document = indexes[0].data(DOCUMENT_ROLE) if indexes else None
        self._details.show_document(document)

    def _update_summary(self) -> None:
        documents = self._model.documents
        total = len(documents)

        self._content.setCurrentIndex(0 if total == 0 and self._running_imports == 0 else 1)

        self._summary.setText(plural(total, "document") if total else "No documents yet")
        self._activity_link.setVisible(self._running_imports > 0)
        self._activity_link.setText(
            f"· {plural(self._running_imports, 'import')} running in the background"
        )

        counts = {key: 0 for key, _ in STATUS_FILTERS}
        counts[FILTER_ALL] = total
        for document in documents:
            counts[STATUS_LOOKS[document.processing_status].group] += 1

        for key, filter_button in self._filter_buttons.items():
            filter_button.setText(f"{filter_button.property('baseText')}  {counts[key]}")

        self._no_matches.setVisible(total > 0 and self._proxy.rowCount() == 0)

    def _confirm_remove(self, document: Document | None) -> None:
        if document is None:
            return

        answer = QMessageBox.question(
            self,
            "Remove from workspace",
            f"Remove “{document.file_name}” from this workspace?\n\n"
            "The original file stays on your computer.",
            QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.Cancel,
        )

        if answer == QMessageBox.StandardButton.Yes:
            self._library.remove_document(document.id)

    def selected_index(self) -> QModelIndex:
        indexes = self._table.selectionModel().selectedRows()
        return indexes[0] if indexes else QModelIndex()
