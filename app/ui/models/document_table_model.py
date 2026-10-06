from __future__ import annotations

from typing import Any

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
    QSortFilterProxyModel,
    Qt,
)

from app.documents.domain import Document
from app.ui.formatting import format_day, format_size
from app.ui.widgets.common import STATUS_LOOKS

ModelIndex = QModelIndex | QPersistentModelIndex

NAME_COLUMN = 0
STATUS_COLUMN = 1
SIZE_COLUMN = 2
ADDED_COLUMN = 3

HEADERS = ["Name", "Status", "Size", "Added"]

DOCUMENT_ROLE = Qt.ItemDataRole.UserRole + 1
SORT_ROLE = Qt.ItemDataRole.UserRole + 2
STATUS_GROUP_ROLE = Qt.ItemDataRole.UserRole + 3

FILTER_ALL = "all"


class DocumentTableModel(QAbstractTableModel):
    """The documents of one workspace, shown in the Library table."""

    def __init__(self) -> None:
        super().__init__()
        self._documents: list[Document] = []

    # Updates -------------------------------------------------------------------

    def set_documents(self, documents: list[Document]) -> None:
        self.beginResetModel()
        self._documents = list(documents)
        self.endResetModel()

    def add_document(self, document: Document) -> None:
        if any(existing.id == document.id for existing in self._documents):
            return

        row = len(self._documents)
        self.beginInsertRows(QModelIndex(), row, row)
        self._documents.append(document)
        self.endInsertRows()

    def remove_document(self, document_id: str) -> None:
        for row, document in enumerate(self._documents):
            if document.id == document_id:
                self.beginRemoveRows(QModelIndex(), row, row)
                del self._documents[row]
                self.endRemoveRows()
                return

    @property
    def documents(self) -> list[Document]:
        return list(self._documents)

    # Qt model interface -----------------------------------------------------------

    def rowCount(self, parent: ModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._documents)

    def columnCount(self, parent: ModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(HEADERS)

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if orientation != Qt.Orientation.Horizontal:
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            return HEADERS[section].upper()

        if role == Qt.ItemDataRole.TextAlignmentRole:
            alignment = Qt.AlignmentFlag.AlignVCenter
            alignment |= (
                Qt.AlignmentFlag.AlignRight if section == SIZE_COLUMN else Qt.AlignmentFlag.AlignLeft
            )
            return alignment

        return None

    def data(self, index: ModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None

        document = self._documents[index.row()]
        column = index.column()

        if role == DOCUMENT_ROLE:
            return document

        if role == STATUS_GROUP_ROLE:
            return STATUS_LOOKS[document.processing_status].group

        if role == Qt.ItemDataRole.DisplayRole:
            if column == NAME_COLUMN:
                return document.file_name
            if column == STATUS_COLUMN:
                return STATUS_LOOKS[document.processing_status].label
            if column == SIZE_COLUMN:
                return format_size(document.file_size)
            if column == ADDED_COLUMN:
                return format_day(document.imported_at)

        if role == SORT_ROLE:
            if column == NAME_COLUMN:
                return document.file_name.casefold()
            if column == STATUS_COLUMN:
                return STATUS_LOOKS[document.processing_status].label
            if column == SIZE_COLUMN:
                return document.file_size
            if column == ADDED_COLUMN:
                return document.imported_at.timestamp()

        if role == Qt.ItemDataRole.ToolTipRole and column == NAME_COLUMN:
            return document.original_path

        if role == Qt.ItemDataRole.TextAlignmentRole:
            alignment = Qt.AlignmentFlag.AlignVCenter
            alignment |= (
                Qt.AlignmentFlag.AlignRight if column == SIZE_COLUMN else Qt.AlignmentFlag.AlignLeft
            )
            return alignment

        return None


class DocumentFilterProxyModel(QSortFilterProxyModel):
    """Filters documents by name and by status group."""

    def __init__(self) -> None:
        super().__init__()
        self._text = ""
        self._status_group = FILTER_ALL
        self.setSortRole(SORT_ROLE)

    def set_text(self, text: str) -> None:
        self.beginFilterChange()
        self._text = text.strip().casefold()
        self.endFilterChange(QSortFilterProxyModel.Direction.Rows)

    def set_status_group(self, group: str) -> None:
        self.beginFilterChange()
        self._status_group = group
        self.endFilterChange(QSortFilterProxyModel.Direction.Rows)

    def filterAcceptsRow(self, source_row: int, source_parent: ModelIndex) -> bool:
        model = self.sourceModel()
        index = model.index(source_row, NAME_COLUMN, source_parent)
        document: Document = model.data(index, DOCUMENT_ROLE)

        if self._text and self._text not in document.file_name.casefold():
            return False

        if self._status_group == FILTER_ALL:
            return True

        return bool(model.data(index, STATUS_GROUP_ROLE) == self._status_group)
