from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError

from app.documents.domain import (
    Document,
    DocumentProcessingStatus,
)
from app.documents.dto.document_import_result import (
    DocumentImportResult,
    DocumentImportStatus,
)
from app.documents.exceptions import DocumentAlreadyImportedError
from app.documents.services.document_service import DocumentService

logger = logging.getLogger(__name__)


class DocumentImportService:
    """Handles importing files into the document system."""

    def __init__(
        self,
        document_service: DocumentService,
    ) -> None:
        self._document_service = document_service

    def import_document(
        self,
        workspace_id: str,
        file_path: Path,
    ) -> Document:
        """Import a single file into a workspace and create its document record."""

        self._validate_file(file_path)

        checksum = self._calculate_checksum(file_path)

        existing_document = self._document_service.find_by_checksum(
            workspace_id,
            checksum,
        )

        if existing_document is not None:
            raise DocumentAlreadyImportedError(
                file_path=str(file_path),
                existing_document_id=existing_document.id,
            )

        document = Document(
            id=str(uuid4()),
            workspace_id=workspace_id,
            file_name=file_path.name,
            original_path=str(file_path),
            file_size=file_path.stat().st_size,
            checksum=checksum,
            file_type=file_path.suffix.lower().lstrip("."),
            imported_at=datetime.now(UTC),
            processing_status=DocumentProcessingStatus.PENDING,
        )

        return self._document_service.create_document(
            document
        )

    def import_documents(
        self,
        workspace_id: str,
        file_paths: Iterable[Path],
    ) -> list[DocumentImportResult]:
        """
        Import multiple files into a workspace independently.

        One failed import does not stop the remaining files
        from being processed.
        """

        results: list[DocumentImportResult] = []

        for file_path in file_paths:
            try:
                document = self.import_document(
                    workspace_id,
                    file_path,
                )

                results.append(
                    DocumentImportResult(
                        file_path=str(file_path),
                        status=DocumentImportStatus.IMPORTED,
                        document=document,
                    )
                )

            except DocumentAlreadyImportedError as error:
                results.append(
                    DocumentImportResult(
                        file_path=str(file_path),
                        status=DocumentImportStatus.ALREADY_IMPORTED,
                        error=str(error),
                    )
                )

            except (OSError, ValueError) as error:
                logger.warning("Failed to import %s: %s", file_path, error)

                results.append(
                    DocumentImportResult(
                        file_path=str(file_path),
                        status=DocumentImportStatus.FAILED,
                        error=str(error),
                    )
                )

            except SQLAlchemyError as error:
                logger.exception("Database error while importing %s", file_path)

                results.append(
                    DocumentImportResult(
                        file_path=str(file_path),
                        status=DocumentImportStatus.FAILED,
                        error=f"Could not save document: {error}",
                    )
                )

        return results

    @staticmethod
    def _validate_file(file_path: Path) -> None:
        """Validate that the import source is a file."""

        if not file_path.exists():
            raise FileNotFoundError(
                f"Document does not exist: {file_path}"
            )

        if not file_path.is_file():
            raise ValueError(
                f"Document path is not a file: {file_path}"
            )

    @staticmethod
    def _calculate_checksum(
        file_path: Path,
    ) -> str:
        """Calculate the SHA-256 checksum of a file."""

        sha256 = hashlib.sha256()

        with file_path.open("rb") as file:
            while chunk := file.read(1024 * 1024):
                sha256.update(chunk)

        return sha256.hexdigest()