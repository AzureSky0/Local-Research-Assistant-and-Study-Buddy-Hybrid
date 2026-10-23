"""Make sure only one Loci runs per data folder.

Two copies started together (easy to do while the first start is slow)
both tried to create the database and crashed with "database is locked".
A lock file in the data folder decides which copy runs; a second copy
asks the first one to show its window, then exits.

On Windows the running copy also holds a named mutex, which the
installer checks so it can ask the user to close Loci before updating.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from PySide6.QtCore import QLockFile, QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

# How long a second copy keeps trying to reach the first one, which may
# still be starting up.
CONNECT_ATTEMPTS = 10
CONNECT_WAIT_MS = 300

# Must match AppMutex in packaging/loci-installer.iss.
WINDOWS_MUTEX_NAME = "LociRunningMutex"


class SingleInstance(QObject):
    """Owns the data folder's lock; reports when another copy asks to be shown."""

    activation_requested = Signal()

    def __init__(self, data_dir: Path, parent: QObject | None = None) -> None:
        super().__init__(parent)
        digest = hashlib.sha256(str(data_dir.resolve()).lower().encode()).hexdigest()[:16]
        self._server_name = f"loci-{digest}"
        # A lock left by a crashed copy is detected (its process is gone) and replaced.
        self._lock = QLockFile(str(data_dir / "loci.lock"))
        self._lock.setStaleLockTime(0)
        self._server: QLocalServer | None = None
        self._mutex: int | None = None

    def acquire(self) -> bool:
        """True if this copy may run; False if another copy already does."""

        if not self._lock.tryLock(0):
            return False

        # This copy holds the lock, so any server left by a crashed copy is stale.
        QLocalServer.removeServer(self._server_name)
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._on_connection)
        self._server.listen(self._server_name)
        self._mutex = create_windows_mutex(WINDOWS_MUTEX_NAME)
        return True

    def ask_running_copy_to_show(self) -> bool:
        """Ask the copy that holds the lock to bring its window to the front."""

        for _ in range(CONNECT_ATTEMPTS):
            socket = QLocalSocket()
            socket.connectToServer(self._server_name)
            if socket.waitForConnected(CONNECT_WAIT_MS):
                socket.write(b"show")
                socket.flush()
                socket.waitForBytesWritten(CONNECT_WAIT_MS)
                socket.disconnectFromServer()
                return True
        return False

    def release(self) -> None:
        if self._server is not None:
            self._server.close()
            self._server = None
        if self._mutex is not None:
            close_windows_handle(self._mutex)
            self._mutex = None
        self._lock.unlock()

    def _on_connection(self) -> None:
        assert self._server is not None
        while (socket := self._server.nextPendingConnection()) is not None:
            socket.disconnected.connect(socket.deleteLater)
        self.activation_requested.emit()


def create_windows_mutex(name: str) -> int | None:
    """Create a named mutex that lives as long as this process (Windows only)."""
    if sys.platform != "win32":
        return None
    import ctypes

    handle = ctypes.windll.kernel32.CreateMutexW(None, False, name)
    return int(handle) or None


def close_windows_handle(handle: int) -> None:
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.kernel32.CloseHandle(handle)
