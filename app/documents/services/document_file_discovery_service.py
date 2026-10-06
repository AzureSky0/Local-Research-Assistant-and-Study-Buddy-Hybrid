from __future__ import annotations

import logging
import os
import stat
from pathlib import Path

from app.documents.dto.document_discovery_result import DocumentDiscoveryResult
from app.documents.supported_formats import is_supported

logger = logging.getLogger(__name__)

# Temporary lock files created by Microsoft Office while a file is open.
OFFICE_LOCK_FILE_PREFIX = "~$"


class DocumentFileDiscoveryService:
    """Finds importable documents inside a folder (FR-DOC-008).

    Hidden and system files are skipped silently. Unsupported files
    and unreadable folders are reported so the user can see what
    was not imported.
    """

    def discover(
        self,
        folder: Path,
        recursive: bool = True,
    ) -> DocumentDiscoveryResult:
        """Scan a folder and sort its files by whether they can be imported."""

        if not folder.exists():
            raise FileNotFoundError(
                f"Folder does not exist: {folder}"
            )

        if not folder.is_dir():
            raise NotADirectoryError(
                f"Path is not a folder: {folder}"
            )

        result = DocumentDiscoveryResult()

        def record_inaccessible(error: OSError) -> None:
            logger.warning("Cannot read folder %s: %s", error.filename, error)
            result.inaccessible_paths.append(Path(error.filename))

        # Symbolic links to folders are not followed, which also
        # prevents infinite loops.
        for current_dir, dir_names, file_names in os.walk(
            folder,
            onerror=record_inaccessible,
        ):
            current_path = Path(current_dir)

            if recursive:
                dir_names[:] = sorted(
                    name
                    for name in dir_names
                    if not self._is_hidden(current_path / name)
                )
            else:
                dir_names.clear()

            for file_name in sorted(file_names):
                file_path = current_path / file_name

                if self._is_hidden(file_path):
                    continue

                if is_supported(file_path):
                    result.supported_files.append(file_path)
                else:
                    result.unsupported_files.append(file_path)

        return result

    @staticmethod
    def _is_hidden(path: Path) -> bool:
        """Return whether a file or folder should be skipped silently."""

        if path.name.startswith((".", OFFICE_LOCK_FILE_PREFIX)):
            return True

        try:
            attributes = getattr(path.stat(), "st_file_attributes", 0)
        except OSError:
            return False

        # Windows hidden and system files (for example desktop.ini, Thumbs.db).
        return bool(
            attributes & (stat.FILE_ATTRIBUTE_HIDDEN | stat.FILE_ATTRIBUTE_SYSTEM)
        )
