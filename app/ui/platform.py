"""Operating-system integration: revealing files and opening folders."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QProcess, QUrl
from PySide6.QtGui import QDesktopServices


def show_in_folder(file_path: Path) -> None:
    """Open the file manager with the file selected (when the OS supports it)."""

    if sys.platform == "win32" and file_path.exists():
        QProcess.startDetached("explorer.exe", [f"/select,{file_path}"])
        return

    if sys.platform == "darwin" and file_path.exists():
        QProcess.startDetached("open", ["-R", str(file_path)])
        return

    open_folder(file_path.parent)


def open_folder(folder: Path) -> None:
    """Open a folder in the system file manager."""

    QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))
