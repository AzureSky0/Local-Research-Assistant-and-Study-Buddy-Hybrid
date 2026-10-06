"""Opens documents in the user's own viewer, at a specific page when possible.

There is no standard way to ask an application to open a PDF at a page,
so the default PDF viewer is identified and given the page in the form
it understands. Unknown viewers still open the file; the caller then
tells the user which page to go to.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QProcess, QUrl
from PySide6.QtGui import QDesktopServices

logger = logging.getLogger(__name__)

# Viewer executable name -> how it accepts a page number.
_ACROBAT = {"acrobat.exe", "acrord32.exe", "acrord64.exe"}
_SUMATRA = {"sumatrapdf.exe"}
_BROWSERS = {"chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe", "vivaldi.exe"}


@dataclass(frozen=True, slots=True)
class OpenResult:
    opened: bool
    at_page: bool  # True when the viewer was asked to show the requested page
    message: str | None = None  # shown to the user when something needs saying


def build_open_command(viewer: Path, document: Path, page: int) -> list[str] | None:
    """Return the command that opens `document` at `page` in `viewer`.

    Returns None for viewers whose page option is unknown.
    """

    name = viewer.name.lower()

    if name in _ACROBAT:
        return [str(viewer), "/A", f"page={page}", str(document)]

    if name in _SUMATRA:
        return [str(viewer), "-page", str(page), str(document)]

    if name in _BROWSERS:
        url = QUrl.fromLocalFile(str(document))
        url.setFragment(f"page={page}")
        return [str(viewer), url.toString()]

    return None


def default_pdf_viewer() -> Path | None:
    """The application Windows uses to open .pdf files, if it can be found."""

    if sys.platform != "win32":
        return None

    import ctypes
    from ctypes import wintypes

    assoc_query = ctypes.windll.shlwapi.AssocQueryStringW  # type: ignore[attr-defined]
    assoc_query.argtypes = [
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
    ]
    assoc_query.restype = ctypes.HRESULT

    assoc_str_executable = 2
    size = wintypes.DWORD(1024)
    buffer = ctypes.create_unicode_buffer(size.value)

    try:
        assoc_query(0, assoc_str_executable, ".pdf", None, buffer, ctypes.byref(size))
    except OSError:
        return None

    return Path(buffer.value) if buffer.value else None


def open_document(path: Path, page: int | None = None) -> OpenResult:
    """Open a document in the user's viewer, at `page` for PDFs when possible."""

    if not path.exists():
        return OpenResult(
            opened=False,
            at_page=False,
            message=f"“{path.name}” is no longer at its saved location. Add it again if it has moved.",
        )

    if page is not None and page > 1 and path.suffix.lower() == ".pdf":
        viewer = default_pdf_viewer()
        command = build_open_command(viewer, path, page) if viewer else None

        if command is not None and QProcess.startDetached(command[0], command[1:]):
            logger.info("Opened %s at page %d with %s", path, page, command[0])
            return OpenResult(opened=True, at_page=True)

        if _open_with_system(path):
            return OpenResult(
                opened=True,
                at_page=False,
                message=f"Opened “{path.name}”. Your PDF viewer can’t jump to a page "
                f"automatically — go to page {page}.",
            )

    elif _open_with_system(path):
        return OpenResult(opened=True, at_page=page is not None)

    return OpenResult(
        opened=False,
        at_page=False,
        message=f"“{path.name}” could not be opened. Check that an app for this file type is installed.",
    )


def _open_with_system(path: Path) -> bool:
    return bool(QDesktopServices.openUrl(QUrl.fromLocalFile(str(path))))
