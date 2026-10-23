"""Make sure only one Loci runs per data folder.

Two copies started together (easy to do while the first start is slow)
both tried to create the database and crashed with "database is locked".
A lock file in the data folder decides which copy runs; a second copy
asks the first one to show its window, then exits.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from PySide6.QtCore import QLockFile, QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

# How long a second copy keeps trying to reach the first one, which may
# still be starting up.
CONNECT_ATTEMPTS = 10
CONNECT_WAIT_MS = 300


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

    def acquire(self) -> bool:
        """True if this copy may run; False if another copy already does."""

        if not self._lock.tryLock(0):
            return False

        # This copy holds the lock, so any server left by a crashed copy is stale.
        QLocalServer.removeServer(self._server_name)
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._on_connection)
        self._server.listen(self._server_name)
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
        self._lock.unlock()

    def _on_connection(self) -> None:
        assert self._server is not None
        while (socket := self._server.nextPendingConnection()) is not None:
            socket.disconnected.connect(socket.deleteLater)
        self.activation_requested.emit()
