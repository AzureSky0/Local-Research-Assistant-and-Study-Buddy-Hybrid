"""Applies the application theme (fonts, palette and stylesheet)."""

from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

from app.ui.theme import tokens as t


def build_stylesheet() -> str:
    """Return the Qt stylesheet built from the design tokens.

    Widgets opt into variants with dynamic properties, for example
    `button.setProperty("variant", "primary")`.
    """

    mono = ", ".join(f'"{family}"' for family in t.MONO_FAMILIES)

    return f"""
    QWidget {{
        color: {t.INK};
        font-size: {t.FONT_SIZE}px;
    }}
    QMainWindow, QWidget#appRoot, QWidget#page, QScrollArea#page > QWidget > QWidget {{
        background: {t.BACKGROUND};
    }}
    QScrollArea {{ border: none; background: transparent; }}

    /* Text roles */
    QLabel[role="title"] {{ font-size: 24px; font-weight: 600; }}
    QLabel[role="hero"] {{ font-size: 28px; font-weight: 600; }}
    QLabel[role="heading"] {{ font-size: 16px; font-weight: 600; }}
    QLabel[role="dialogTitle"] {{ font-size: 20px; font-weight: 600; }}
    QLabel[role="muted"] {{ color: {t.MUTED}; }}
    QLabel[role="small"] {{ color: {t.MUTED}; font-size: 13px; }}
    QLabel[role="section"] {{
        color: {t.MUTED}; font-size: 12px; font-weight: 500; letter-spacing: 0.5px;
    }}
    QLabel[role="mono"] {{ font-family: {mono}; font-size: 12px; color: {t.SUBTLE}; }}
    QLabel[role="badge"] {{
        font-family: {mono}; font-size: 11px; font-weight: 500;
        border-radius: 4px; padding: 2px 6px;
    }}
    QLabel[role="chip"] {{
        font-size: 12px; font-weight: 500; border-radius: 12px; padding: 3px 10px;
    }}

    /* Surfaces */
    QFrame[surface="card"] {{
        background: {t.SURFACE}; border: 1px solid {t.BORDER}; border-radius: 12px;
    }}
    QFrame[surface="panel"] {{
        background: {t.SURFACE}; border: none; border-left: 1px solid {t.BORDER};
    }}
    QFrame[surface="sidebar"] {{
        background: {t.SURFACE}; border: none; border-right: 1px solid {t.BORDER};
    }}
    QFrame[surface="header"] {{
        background: {t.SURFACE}; border: none; border-bottom: 1px solid {t.BORDER};
    }}
    QFrame[surface="dropzone"] {{
        background: {t.SURFACE}; border: 2px dashed {t.ACCENT_DASHED}; border-radius: 16px;
    }}
    QFrame[surface="dropzone"][dragActive="true"] {{
        background: {t.ACCENT_SOFT}; border-color: {t.ACCENT};
    }}
    QFrame[surface="input"] {{
        background: {t.SURFACE}; border: 1px solid {t.BORDER_STRONG}; border-radius: 8px;
    }}
    QFrame[surface="divider"] {{ background: {t.BORDER}; max-height: 1px; border: none; }}

    /* Buttons */
    QPushButton, QToolButton {{
        min-height: 40px; padding: 0 14px; border-radius: 8px;
        border: 1px solid {t.BORDER_STRONG}; background: {t.SURFACE};
        font-size: 14px;
    }}
    QPushButton:hover, QToolButton:hover {{ background: {t.BACKGROUND}; }}
    QPushButton:focus, QToolButton:focus {{ border: 2px solid {t.ACCENT}; }}
    QPushButton:disabled {{ color: {t.MUTED}; background: {t.NEUTRAL_SOFT}; }}

    QPushButton[variant="primary"] {{
        min-height: 44px; padding: 0 18px; border: none;
        background: {t.ACCENT}; color: #FFFFFF; font-weight: 500; font-size: 15px;
    }}
    QPushButton[variant="primary"]:hover {{ background: {t.ACCENT_HOVER}; }}
    QPushButton[variant="primary"]:pressed {{ background: {t.ACCENT_PRESSED}; }}
    QPushButton[variant="primary"]:focus {{ border: 2px solid {t.INK}; }}
    QPushButton[variant="primary"]:disabled {{ background: {t.ACCENT_DASHED}; color: #FFFFFF; }}

    QPushButton[variant="secondary"] {{ min-height: 44px; font-size: 15px; font-weight: 500; }}
    QPushButton[size="small"] {{ min-height: 36px; padding: 0 12px; font-size: 13px; }}

    QPushButton[variant="danger"] {{
        border: 1px solid {t.DANGER_BORDER}; color: {t.DANGER};
    }}
    QPushButton[variant="link"] {{
        border: none; background: transparent; color: {t.ACCENT};
        font-weight: 500; padding: 0; min-height: 28px;
    }}
    QPushButton[variant="link"]:hover {{ color: {t.ACCENT_PRESSED}; text-decoration: underline; }}
    QPushButton[variant="ghost"] {{
        border: none; background: transparent; color: {t.MUTED};
        padding: 0 8px; min-height: 32px; text-align: left;
    }}
    QPushButton[variant="ghost"]:hover {{ color: {t.INK}; }}

    QPushButton[variant="nav"] {{
        border: none; background: transparent; color: {t.SUBTLE};
        text-align: left; padding: 0 12px; min-height: 40px;
    }}
    QPushButton[variant="nav"]:hover {{ background: {t.BACKGROUND}; }}
    QPushButton[variant="nav"]:checked {{
        background: {t.ACCENT_SOFT}; color: {t.ACCENT_PRESSED}; font-weight: 500;
    }}

    QPushButton[variant="filter"] {{
        min-height: 36px; padding: 0 12px; border-radius: 18px; font-size: 13px; font-weight: 500;
        color: {t.SUBTLE};
    }}
    QPushButton[variant="filter"]:checked {{
        background: {t.INK}; color: #FFFFFF; border-color: {t.INK};
    }}

    QPushButton[variant="workspaceCard"] {{
        background: {t.SURFACE}; border: 1px solid {t.BORDER}; border-radius: 12px;
        padding: 0; text-align: left; min-height: 148px; max-height: 148px;
    }}
    QPushButton[variant="workspaceCard"]:hover {{ border-color: {t.ACCENT_DASHED}; }}
    QPushButton[variant="workspaceCard"]:focus {{ border: 2px solid {t.ACCENT}; }}
    QPushButton[variant="createCard"] {{
        background: transparent; border: 2px dashed {t.ACCENT_DASHED}; border-radius: 12px;
        color: {t.ACCENT}; font-weight: 500; font-size: 15px;
        min-height: 146px; max-height: 146px;
    }}
    QPushButton[variant="createCard"]:hover {{ background: {t.ACCENT_SOFT}; }}

    QPushButton[variant="swatch"] {{
        min-height: 44px; min-width: 44px; max-width: 44px; padding: 0;
        border-radius: 10px; border: 2px solid transparent;
    }}
    QPushButton[variant="swatch"]:checked {{ border: 2px solid {t.INK}; }}

    QToolButton[variant="workspaceSwitcher"] {{
        min-height: 56px; padding: 6px 10px; border-radius: 10px; text-align: left;
    }}
    QToolButton[variant="icon"] {{
        min-height: 32px; min-width: 32px; padding: 0; border: none; background: transparent;
    }}
    QToolButton[variant="icon"]:hover {{ background: {t.NEUTRAL_SOFT}; }}
    QToolButton::menu-indicator {{ image: none; width: 0; }}

    /* Inputs */
    QLineEdit {{
        min-height: 40px; padding: 0 12px; border: 1px solid {t.BORDER_STRONG};
        border-radius: 8px; background: {t.SURFACE}; font-size: 14px;
        selection-background-color: {t.ACCENT_SOFT}; selection-color: {t.INK};
    }}
    QLineEdit:focus {{ border: 2px solid {t.ACCENT}; padding: 0 11px; }}
    QLineEdit[embedded="true"], QLineEdit[embedded="true"]:focus {{
        border: none; padding: 0; background: transparent; min-height: 38px;
    }}
    QLineEdit[size="large"] {{ min-height: 44px; font-size: 15px; }}

    /* Table */
    QTableView {{
        background: {t.SURFACE}; border: 1px solid {t.BORDER}; border-radius: 12px;
        gridline-color: transparent; selection-background-color: {t.ACCENT_SELECTED_ROW};
        selection-color: {t.INK}; outline: none;
    }}
    QTableView::item {{ border-bottom: 1px solid {t.DIVIDER}; padding: 0 12px; }}
    QTableView::item:selected {{ background: {t.ACCENT_SELECTED_ROW}; color: {t.INK}; }}
    QHeaderView::section {{
        background: {t.SURFACE}; color: {t.MUTED}; border: none;
        border-bottom: 1px solid {t.BORDER}; padding: 10px 12px;
        font-size: 12px; font-weight: 500;
    }}

    /* Progress */
    QProgressBar {{
        border: none; border-radius: 4px; background: {t.BORDER};
        max-height: 8px; min-height: 8px; text-align: center; color: transparent;
    }}
    QProgressBar::chunk {{ border-radius: 4px; background: {t.ACCENT}; }}

    /* Menus and dialogs */
    QMenu {{
        background: {t.SURFACE}; border: 1px solid {t.BORDER}; border-radius: 8px; padding: 6px;
    }}
    QMenu::item {{ padding: 8px 16px; border-radius: 6px; }}
    QMenu::item:selected {{ background: {t.ACCENT_SOFT}; color: {t.INK}; }}
    QMenu::separator {{ height: 1px; background: {t.BORDER}; margin: 6px 4px; }}
    QDialog {{ background: {t.SURFACE}; }}

    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: {t.BORDER_STRONG}; border-radius: 4px; min-height: 32px; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
    QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
    QScrollBar::handle:horizontal {{ background: {t.BORDER_STRONG}; border-radius: 4px; min-width: 32px; }}

    QWidget#toast {{ background: {t.TOAST_BACKGROUND}; border-radius: 12px; }}
    QWidget#toast QLabel {{ color: {t.TOAST_TEXT}; }}
    QWidget#toast QPushButton {{
        border: none; background: transparent; color: {t.TOAST_LINK};
        font-weight: 500; min-height: 28px; padding: 0 4px;
    }}
    """


def mono_font(point_size: int | None = None) -> QFont:
    """Return the monospace font used for numbers, sizes and paths."""

    font = QFont()
    font.setFamilies(t.MONO_FAMILIES)
    font.setStyleHint(QFont.StyleHint.Monospace)

    if point_size is not None:
        font.setPixelSize(point_size)

    return font


def apply_theme(app: QApplication) -> None:
    """Apply fonts, palette and stylesheet to the application."""

    app.setStyle("Fusion")

    font = QFont()
    font.setFamilies(t.FONT_FAMILIES)
    font.setPixelSize(t.FONT_SIZE)
    app.setFont(font)

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(t.BACKGROUND))
    palette.setColor(QPalette.ColorRole.Base, QColor(t.SURFACE))
    palette.setColor(QPalette.ColorRole.Text, QColor(t.INK))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(t.INK))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(t.INK))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(t.ACCENT_SOFT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(t.INK))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(t.MUTED))
    app.setPalette(palette)

    app.setStyleSheet(build_stylesheet())
