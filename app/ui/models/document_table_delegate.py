from __future__ import annotations

from PySide6.QtCore import QModelIndex, QPersistentModelIndex, QRect, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import QStyle, QStyledItemDelegate, QStyleOptionViewItem

from app.documents.domain import Document
from app.ui.models.document_table_model import (
    DOCUMENT_ROLE,
    NAME_COLUMN,
    SIZE_COLUMN,
    STATUS_COLUMN,
)
from app.ui.theme import mono_font
from app.ui.theme import tokens as t
from app.ui.theme.icons import icon_pixmap
from app.ui.widgets.common import STATUS_LOOKS

ROW_HEIGHT = 46
PADDING = 16


class DocumentTableDelegate(QStyledItemDelegate):
    """Paints file-type badges, status chips and row dividers."""

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex) -> QSize:
        size = super().sizeHint(option, index)
        return QSize(size.width(), ROW_HEIGHT)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        document: Document = index.data(DOCUMENT_ROLE)
        rect = option.rect  # type: ignore[attr-defined]
        selected = bool(option.state & QStyle.StateFlag.State_Selected)  # type: ignore[attr-defined]

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(rect, QColor(t.ACCENT_SELECTED_ROW if selected else t.SURFACE))
        painter.setPen(QColor(t.DIVIDER))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())

        column = index.column()

        if column == NAME_COLUMN:
            self._paint_name(painter, rect, document, selected, option.font)  # type: ignore[attr-defined]
        elif column == STATUS_COLUMN:
            self._paint_status(painter, rect, document)
        elif column == SIZE_COLUMN:
            self._paint_text(painter, rect, index.data(), mono_font(13), t.MUTED, right=True)
        else:
            self._paint_text(painter, rect, index.data(), option.font, t.MUTED)  # type: ignore[attr-defined]

        painter.restore()

    # Columns ----------------------------------------------------------------------

    def _paint_name(
        self,
        painter: QPainter,
        rect: QRect,
        document: Document,
        selected: bool,
        base_font: QFont,
    ) -> None:
        swatch = t.file_type_swatch(document.file_type)

        badge_font = mono_font(11)
        badge_font.setWeight(QFont.Weight.Medium)
        badge = QRectF(rect.left() + PADDING, rect.center().y() - 9, 36, 18)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(swatch.tint))
        painter.drawRoundedRect(badge, 4, 4)
        painter.setFont(badge_font)
        painter.setPen(QColor(swatch.color))
        painter.drawText(badge, Qt.AlignmentFlag.AlignCenter, swatch.label)

        name_font = QFont(base_font)
        if selected:
            name_font.setWeight(QFont.Weight.DemiBold)

        text_rect = QRect(rect)
        text_rect.setLeft(int(badge.right()) + 10)
        text_rect.setRight(rect.right() - PADDING)
        self._paint_text(painter, text_rect, document.file_name, name_font, t.INK, padding=0)

    def _paint_status(self, painter: QPainter, rect: QRect, document: Document) -> None:
        look = STATUS_LOOKS[document.processing_status]
        swatch = look.swatch

        font = QFont(painter.font())
        font.setPixelSize(12)
        font.setWeight(QFont.Weight.Medium)
        text_width = QFontMetrics(font).horizontalAdvance(look.label)

        chip = QRectF(rect.left() + PADDING, rect.center().y() - 12, 9 + 12 + 6 + text_width + 10, 24)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(swatch.tint))
        painter.drawRoundedRect(chip, 12, 12)

        painter.drawPixmap(
            int(chip.left()) + 9,
            int(chip.center().y()) - 6,
            icon_pixmap(look.icon, swatch.color, 12, 3.0),
        )

        painter.setFont(font)
        painter.setPen(QColor(swatch.color))
        painter.drawText(
            chip.adjusted(9 + 12 + 6, 0, 0, 0),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            look.label,
        )

    @staticmethod
    def _paint_text(
        painter: QPainter,
        rect: QRect,
        text: str,
        font: QFont,
        color: str,
        right: bool = False,
        padding: int = PADDING,
    ) -> None:
        painter.setFont(font)
        painter.setPen(QColor(color))

        area = rect.adjusted(padding, 0, -padding, 0)
        elided = QFontMetrics(font).elidedText(text, Qt.TextElideMode.ElideRight, area.width())
        alignment = Qt.AlignmentFlag.AlignVCenter | (
            Qt.AlignmentFlag.AlignRight if right else Qt.AlignmentFlag.AlignLeft
        )
        painter.drawText(area, alignment, elided)
