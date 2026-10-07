"""Search results in the Library: matching file names and passages."""

from __future__ import annotations

import html
from enum import IntEnum

from PySide6.QtCore import QModelIndex, QPersistentModelIndex, QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QAbstractTextDocumentLayout,
    QColor,
    QFont,
    QFontMetrics,
    QPainter,
    QPalette,
    QStandardItem,
    QStandardItemModel,
    QTextDocument,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QListView,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QVBoxLayout,
    QWidget,
)

from app.knowledge.dto.search_results import (
    HIGHLIGHT_END,
    HIGHLIGHT_START,
    SearchResults,
)
from app.ui.formatting import plural
from app.ui.theme import mono_font
from app.ui.theme import tokens as t
from app.ui.widgets.common import label

KIND_ROLE = Qt.ItemDataRole.UserRole + 1
DOCUMENT_ID_ROLE = Qt.ItemDataRole.UserRole + 2
FILE_NAME_ROLE = Qt.ItemDataRole.UserRole + 3
FILE_TYPE_ROLE = Qt.ItemDataRole.UserRole + 4
PAGE_ROLE = Qt.ItemDataRole.UserRole + 5
SNIPPET_HTML_ROLE = Qt.ItemDataRole.UserRole + 6
END_PAGE_ROLE = Qt.ItemDataRole.UserRole + 7
MATCHED_BY_ROLE = Qt.ItemDataRole.UserRole + 8

HIGHLIGHT_COLOR = "#FFE9A8"
PADDING_X = 18
PADDING_Y = 12
LINE_GAP = 6
BADGE_WIDTH = 36


class RowKind(IntEnum):
    SECTION = 0
    NAME = 1
    PASSAGE = 2
    MORE = 3  # "N more matching pages in this document"


def snippet_to_html(snippet: str) -> str:
    """Escape a snippet and turn highlight markers into styled spans."""

    escaped = html.escape(" ".join(snippet.split()))
    return escaped.replace(
        HIGHLIGHT_START,
        f'<span style="background-color:{HIGHLIGHT_COLOR}; font-weight:600;">',
    ).replace(HIGHLIGHT_END, "</span>")


class SearchResultsDelegate(QStyledItemDelegate):
    """Paints section titles, file-name matches and passages with snippets."""

    def __init__(self, view: QListView) -> None:
        super().__init__(view)
        self._view = view

    # Layout ------------------------------------------------------------------------

    def sizeHint(
        self,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> QSize:
        width = self._view.viewport().width()
        kind = index.data(KIND_ROLE)

        if kind == RowKind.SECTION:
            return QSize(width, 40)

        if kind == RowKind.MORE:
            return QSize(width, 34)

        if kind == RowKind.NAME:
            return QSize(width, 48)

        document = self._snippet_document(index, width)
        title_height = QFontMetrics(self._view.font()).height()
        height = PADDING_Y + title_height + LINE_GAP + int(document.size().height()) + PADDING_Y
        return QSize(width, height)

    def _snippet_document(self, index: QModelIndex | QPersistentModelIndex, width: int) -> QTextDocument:
        document = QTextDocument()
        document.setDocumentMargin(0)
        font = QFont(self._view.font())
        font.setPixelSize(13)
        document.setDefaultFont(font)
        document.setDefaultStyleSheet(f"body {{ color: {t.SUBTLE}; }}")
        document.setHtml(f"<body>{index.data(SNIPPET_HTML_ROLE)}</body>")
        document.setTextWidth(max(width - 2 * PADDING_X, 100))
        return document

    # Painting ------------------------------------------------------------------------

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        rect: QRect = option.rect  # type: ignore[attr-defined]
        state = option.state  # type: ignore[attr-defined]
        kind = index.data(KIND_ROLE)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if kind == RowKind.SECTION:
            self._paint_section(painter, rect, index.data(Qt.ItemDataRole.DisplayRole))
            painter.restore()
            return

        if kind == RowKind.MORE:
            self._paint_more(painter, rect, index.data(Qt.ItemDataRole.DisplayRole))
            painter.restore()
            return

        if state & QStyle.StateFlag.State_Selected:
            painter.fillRect(rect, QColor(t.ACCENT_SELECTED_ROW))
        elif state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(rect, QColor(t.BACKGROUND))
        else:
            painter.fillRect(rect, QColor(t.SURFACE))

        painter.setPen(QColor(t.DIVIDER))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())

        title_height = QFontMetrics(self._view.font()).height()
        top = rect.top() + (PADDING_Y if kind == RowKind.PASSAGE else (rect.height() - title_height) // 2)
        title_rect = QRect(rect.left() + PADDING_X, top, rect.width() - 2 * PADDING_X, title_height)

        self._paint_title(painter, title_rect, index)

        if kind == RowKind.PASSAGE:
            document = self._snippet_document(index, rect.width())
            painter.translate(rect.left() + PADDING_X, title_rect.bottom() + LINE_GAP)
            context = QAbstractTextDocumentLayout.PaintContext()
            context.palette.setColor(QPalette.ColorRole.Text, QColor(t.SUBTLE))
            document.documentLayout().draw(painter, context)

        painter.restore()

    def _paint_section(self, painter: QPainter, rect: QRect, text: str) -> None:
        painter.fillRect(rect, QColor(t.BACKGROUND))
        font = QFont(self._view.font())
        font.setPixelSize(12)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)
        painter.setPen(QColor(t.MUTED))
        painter.drawText(
            rect.adjusted(PADDING_X, 0, -PADDING_X, -6),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom,
            text.upper(),
        )

    def _paint_more(self, painter: QPainter, rect: QRect, text: str) -> None:
        painter.fillRect(rect, QColor(t.SURFACE))
        painter.setPen(QColor(t.DIVIDER))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())
        font = QFont(self._view.font())
        font.setPixelSize(12)
        painter.setFont(font)
        painter.setPen(QColor(t.MUTED))
        painter.drawText(
            rect.adjusted(PADDING_X + BADGE_WIDTH + 10, 0, -PADDING_X, 0),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            text,
        )

    def _paint_title(self, painter: QPainter, rect: QRect, index: QModelIndex | QPersistentModelIndex) -> None:
        swatch = t.file_type_swatch(index.data(FILE_TYPE_ROLE))

        badge = QRectF(rect.left(), rect.center().y() - 9, BADGE_WIDTH, 18)
        badge_font = mono_font(11)
        badge_font.setWeight(QFont.Weight.Medium)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(swatch.tint))
        painter.drawRoundedRect(badge, 4, 4)
        painter.setFont(badge_font)
        painter.setPen(QColor(swatch.color))
        painter.drawText(badge, Qt.AlignmentFlag.AlignCenter, swatch.label)

        page = index.data(PAGE_ROLE)
        end_page = index.data(END_PAGE_ROLE)
        if page and end_page:
            page_text = f"Pages {page}–{end_page}"
        elif page:
            page_text = f"Page {page}"
        else:
            page_text = ""

        # Passages that share no words with the search were found by meaning.
        if index.data(MATCHED_BY_ROLE) == "meaning":
            page_text = f"by meaning · {page_text}" if page_text else "by meaning"

        name_font = QFont(self._view.font())
        name_font.setWeight(QFont.Weight.DemiBold)
        page_font = QFont(self._view.font())
        page_font.setPixelSize(13)

        page_width = QFontMetrics(page_font).horizontalAdvance(page_text) if page_text else 0
        name_rect = QRect(rect)
        name_rect.setLeft(int(badge.right()) + 10)
        name_rect.setRight(rect.right() - page_width - (12 if page_text else 0))

        painter.setFont(name_font)
        painter.setPen(QColor(t.INK))
        name = QFontMetrics(name_font).elidedText(
            index.data(FILE_NAME_ROLE), Qt.TextElideMode.ElideMiddle, name_rect.width()
        )
        painter.drawText(name_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, name)

        if page_text:
            painter.setFont(page_font)
            painter.setPen(QColor(t.MUTED))
            painter.drawText(rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, page_text)


class SearchResultsView(QWidget):
    """Shows what a search found; selecting a row selects that document."""

    document_selected = Signal(str, object)  # document id, page (int | None)
    open_requested = Signal(str, object)  # document id, page (int | None)

    def __init__(self) -> None:
        super().__init__()

        self._summary = label("", "muted")
        self._note = label("", "small", wrap=True)
        self._note.hide()

        self._model = QStandardItemModel(self)

        self._list = QListView()
        self._list.setModel(self._model)
        self._list.setItemDelegate(SearchResultsDelegate(self._list))
        self._list.setResizeMode(QListView.ResizeMode.Adjust)
        self._list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._list.setMouseTracking(True)
        self._list.setFrameShape(QFrame.Shape.NoFrame)
        self._list.setStyleSheet(
            f"QListView {{ background: {t.SURFACE}; border: 1px solid {t.BORDER}; border-radius: 12px; }}"
        )
        self._list.setAccessibleName("Search results")
        self._list.setToolTip("Double-click or press Enter to open at this page")
        self._list.clicked.connect(self._on_clicked)
        # Double-click or Enter.
        self._list.activated.connect(self._on_activated)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(self._summary)
        layout.addWidget(self._note)
        layout.addWidget(self._list, 1)

    @property
    def row_count(self) -> int:
        return self._model.rowCount()

    def show_results(self, results: SearchResults, documents_still_reading: int) -> None:
        self._model.clear()

        if results.is_empty:
            self._summary.setText(f"No matches for “{results.query}”.")
        elif results.used_meaning:
            documents = len({passage.document_id for passage in results.passages})
            parts = [f"Best matches in {plural(documents, 'document')}, by words and meaning"]
            if results.name_matches:
                parts.append(f"{plural(len(results.name_matches), 'file name')}")
            self._summary.setText(" · ".join(parts))
        else:
            parts = []
            if results.passages:
                parts.append(
                    f"{plural(results.total_passages, 'page')} in "
                    f"{plural(results.total_documents, 'document')}"
                    + (" — best matches first" if results.total_passages > len(results.passages) else "")
                )
            if results.name_matches:
                parts.append(f"{plural(len(results.name_matches), 'file name')}")
            self._summary.setText(" · ".join(parts))

        notes = []
        done, total = results.meaning_progress
        if results.used_meaning and total and done < total:
            notes.append(
                f"Search by meaning covers {done * 100 // total}% of passages so far "
                "— results will improve as it finishes."
            )
        if results.too_common:
            notes.append(
                "Words like these appear on almost every page — add a more specific word."
            )
        elif results.widened and not results.used_meaning:
            notes.append(
                "No page contains all your words — showing the closest matches."
            )
        elif results.match_mode == "any" and results.passages and not results.used_meaning:
            notes.append("Showing pages that contain most of your words, best matches first.")
        if documents_still_reading > 0:
            notes.append(
                f"{plural(documents_still_reading, 'document')} still being read "
                "— they will appear in search once they are ready."
            )

        self._note.setVisible(bool(notes))
        self._note.setText("\n".join(notes))

        if results.name_matches:
            self._add_section("File names")
            for match in results.name_matches:
                self._add_row(RowKind.NAME, match.document_id, match.file_name, match.file_type)

        if results.passages:
            self._add_section("Inside documents")
            for position, passage in enumerate(results.passages):
                self._add_row(
                    RowKind.PASSAGE,
                    passage.document_id,
                    passage.file_name,
                    passage.file_type,
                    # Text and Markdown files are a single page.
                    page=passage.page_number if passage.file_type == "pdf" else None,
                    end_page=passage.end_page if passage.file_type == "pdf" else None,
                    matched_by=passage.matched_by,
                    snippet_html=snippet_to_html(passage.snippet),
                    tooltip=f"{passage.file_name}, page {passage.page_number}",
                )

                # After a document's last shown page, say how many more match.
                is_last_of_document = (
                    position + 1 == len(results.passages)
                    or results.passages[position + 1].document_id != passage.document_id
                )
                shown = sum(1 for p in results.passages if p.document_id == passage.document_id)
                hidden = passage.pages_in_document - shown

                if is_last_of_document and hidden > 0:
                    more = QStandardItem(
                        f"{plural(hidden, 'more matching page')} in this document"
                    )
                    more.setData(RowKind.MORE, KIND_ROLE)
                    more.setFlags(Qt.ItemFlag.NoItemFlags)
                    self._model.appendRow(more)

    def clear_selection(self) -> None:
        self._list.clearSelection()

    def _add_section(self, title: str) -> None:
        item = QStandardItem(title)
        item.setData(RowKind.SECTION, KIND_ROLE)
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        self._model.appendRow(item)

    def _add_row(
        self,
        kind: RowKind,
        document_id: str,
        file_name: str,
        file_type: str,
        page: int | None = None,
        snippet_html: str = "",
        tooltip: str | None = None,
        end_page: int | None = None,
        matched_by: str = "words",
    ) -> None:
        item = QStandardItem(file_name)
        item.setData(kind, KIND_ROLE)
        item.setData(document_id, DOCUMENT_ID_ROLE)
        item.setData(file_name, FILE_NAME_ROLE)
        item.setData(file_type, FILE_TYPE_ROLE)
        item.setData(page, PAGE_ROLE)
        item.setData(snippet_html, SNIPPET_HTML_ROLE)
        item.setData(end_page, END_PAGE_ROLE)
        item.setData(matched_by, MATCHED_BY_ROLE)
        item.setToolTip(tooltip or file_name)
        item.setEditable(False)
        self._model.appendRow(item)

    def _on_clicked(self, index: QModelIndex) -> None:
        document_id = index.data(DOCUMENT_ID_ROLE)

        if document_id:
            self.document_selected.emit(document_id, index.data(PAGE_ROLE))

    def _on_activated(self, index: QModelIndex) -> None:
        document_id = index.data(DOCUMENT_ID_ROLE)

        if document_id:
            self.document_selected.emit(document_id, index.data(PAGE_ROLE))
            self.open_requested.emit(document_id, index.data(PAGE_ROLE))
