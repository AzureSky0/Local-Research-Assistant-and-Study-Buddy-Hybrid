"""The application logo: an open book with a place marker.

Your library, and the place in it. A placeholder logo, to be redesigned
after v0.4 or v0.5. The same drawing is used for the window, the
start-up screen and (via scripts/make_app_icon.py) Loci.exe and the installer.
"""

from __future__ import annotations

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

APP_ICON_SVG = """\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#4766E0"/>
      <stop offset="1" stop-color="#2639A8"/>
    </linearGradient>
  </defs>
  <rect x="8" y="8" width="240" height="240" rx="56" fill="url(#bg)"/>
  <path d="M124 100 C104 88 76 84 48 88 V192 C76 188 104 192 124 204 Z" fill="#FFFFFF"/>
  <path d="M132 100 C152 88 180 84 208 88 V192 C180 188 152 192 132 204 Z" fill="#FFFFFF"/>
  <path d="M128 36 C110 36 98 49 98 65 C98 86 128 112 128 112 C128 112 158 86 158 65 \
C158 49 146 36 128 36 Z" fill="#F5B342"/>
  <circle cx="128" cy="64" r="10" fill="#2F4FCB"/>
</svg>
"""

# Sizes Windows uses for app icons (taskbar, Start, Explorer views).
ICON_SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)


def app_icon_pixmap(size: int) -> QPixmap:
    """The logo drawn at exactly size x size pixels, with a transparent background."""
    renderer = QSvgRenderer(QByteArray(APP_ICON_SVG.encode()))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    return pixmap


def app_icon() -> QIcon:
    """The window icon, drawn sharply at every size Windows asks for."""
    icon = QIcon()
    for size in ICON_SIZES:
        icon.addPixmap(app_icon_pixmap(size))
    return icon
