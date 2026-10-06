from __future__ import annotations

from pathlib import Path

from app.documents.supported_formats import SUPPORTED_FORMATS_DESCRIPTION


class DocumentError(Exception):
    """Base exception for document-related application errors."""


class DocumentAlreadyImportedError(DocumentError):
    """Raised when a document has already been imported."""

    def __init__(
        self,
        file_path: str,
        existing_document_id: str,
    ) -> None:
        self.file_path = file_path
        self.existing_document_id = existing_document_id

        super().__init__(
            f"Document has already been imported: {file_path}"
        )


class UnsupportedDocumentTypeError(DocumentError):
    """Raised when a file's format is not supported."""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

        path = Path(file_path)
        suffix = path.suffix.lower()

        detected = (
            f"a {suffix} file"
            if suffix
            else "a file without an extension"
        )

        super().__init__(
            f"{path.name} is {detected}, which is not supported yet. "
            f"Supported formats: {SUPPORTED_FORMATS_DESCRIPTION}."
        )


class InvalidDocumentError(DocumentError):
    """Raised when a file has a supported extension but invalid content."""

    def __init__(
        self,
        file_path: str,
        reason: str,
    ) -> None:
        self.file_path = file_path
        self.reason = reason

        super().__init__(
            f"{Path(file_path).name} cannot be imported: {reason}"
        )
