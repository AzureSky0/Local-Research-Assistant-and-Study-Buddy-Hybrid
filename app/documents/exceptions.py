from __future__ import annotations


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