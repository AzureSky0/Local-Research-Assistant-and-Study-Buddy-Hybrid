"""Stroke icons rendered from inline SVG, tinted to any color."""

from __future__ import annotations

from functools import lru_cache

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

# 24x24 stroke paths (same shapes as the design canvas).
_ICON_PATHS: dict[str, str] = {
    "book": '<path d="M4 19.5V5a2 2 0 0 1 2-2h12v16H6a2 2 0 0 0-2 2.5z"/><path d="M8 7h6"/>',
    "folder": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "file": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    "chevron-left": '<path d="m15 18-6-6 6-6"/>',
    "chevron-down": '<path d="m7 10 5 5 5-5"/>',
    "activity": '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    "settings": (
        '<circle cx="12" cy="12" r="3"/>'
        '<path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3'
        'M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/>'
    ),
    "upload": '<path d="M12 16V4"/><path d="m7 9 5-5 5 5"/><path d="M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/>',
    "lock": '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "spinner": '<path d="M21 12a9 9 0 1 1-6.2-8.6"/>',
    "alert": '<path d="M12 3 2 21h20z"/><path d="M12 10v4M12 17.5v.5"/>',
    "skip": '<circle cx="12" cy="12" r="9"/><path d="M8 12h8"/>',
    "trash": '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/>',
    "close": '<path d="M6 6l12 12M18 6 6 18"/>',
    "more": '<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>',
    "stop": '<rect x="6" y="6" width="12" height="12" rx="2"/>',
}


def _svg(name: str, color: str, stroke_width: float) -> bytes:
    paths = _ICON_PATHS[name]
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" '
        f'stroke-linejoin="round">{paths}</svg>'
    ).encode()


@lru_cache(maxsize=256)
def icon_pixmap(
    name: str,
    color: str,
    size: int = 18,
    stroke_width: float = 2.0,
    device_pixel_ratio: float = 2.0,
) -> QPixmap:
    """Render an icon to a crisp pixmap of `size` logical pixels."""

    renderer = QSvgRenderer(QByteArray(_svg(name, color, stroke_width)))

    physical = int(size * device_pixel_ratio)
    pixmap = QPixmap(physical, physical)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter, QRectF(0, 0, physical, physical))
    painter.end()

    pixmap.setDevicePixelRatio(device_pixel_ratio)
    return pixmap


def icon(name: str, color: str, size: int = 18, stroke_width: float = 2.0) -> QIcon:
    """Return a QIcon for buttons and menus."""
    return QIcon(icon_pixmap(name, color, size, stroke_width))
