from __future__ import annotations

from pathlib import Path

from app.documents.exceptions import (
    InvalidDocumentError,
    UnsupportedDocumentTypeError,
)
from app.documents.supported_formats import (
    PDF,
    TEXT_FILE_TYPES,
    get_file_type,
)

PDF_SIGNATURE = b"%PDF-"

# The PDF specification allows the header to appear anywhere
# in the first 1024 bytes.
PDF_HEADER_SEARCH_BYTES = 1024

TEXT_SAMPLE_BYTES = 8192

UTF16_BOMS = (b"\xff\xfe", b"\xfe\xff")


class DocumentFileValidator:
    """Validates a file before it is imported (FR-DOC-002).

    Checks run from cheapest to most expensive, and all of them
    run before the file is checksummed or processed.
    """

    def validate(self, file_path: Path) -> str:
        """Validate a file and return its document file type."""

        if not file_path.exists():
            raise FileNotFoundError(
                f"Document does not exist: {file_path}"
            )

        if not file_path.is_file():
            raise ValueError(
                f"Document path is not a file: {file_path}"
            )

        file_type = get_file_type(file_path)

        if file_type is None:
            raise UnsupportedDocumentTypeError(str(file_path))

        if file_path.stat().st_size == 0:
            raise InvalidDocumentError(
                str(file_path),
                "the file is empty.",
            )

        sample = self._read_sample(file_path)

        if file_type == PDF and not self._looks_like_pdf(sample):
            raise InvalidDocumentError(
                str(file_path),
                "the file has a .pdf extension but is not a valid PDF.",
            )

        if file_type in TEXT_FILE_TYPES and not self._looks_like_text(sample):
            raise InvalidDocumentError(
                str(file_path),
                "the file does not appear to contain text.",
            )

        return file_type

    @staticmethod
    def _read_sample(file_path: Path) -> bytes:
        """Read the first bytes of a file for content checks."""

        with file_path.open("rb") as file:
            return file.read(TEXT_SAMPLE_BYTES)

    @staticmethod
    def _looks_like_pdf(sample: bytes) -> bool:
        """Return whether the sample contains a PDF header."""

        return PDF_SIGNATURE in sample[:PDF_HEADER_SEARCH_BYTES]

    @staticmethod
    def _looks_like_text(sample: bytes) -> bool:
        """Return whether the sample looks like text rather than binary data.

        Binary files almost always contain NUL bytes. UTF-16 text also
        contains NUL bytes, so files starting with a UTF-16 byte order
        mark are accepted.
        """

        if sample.startswith(UTF16_BOMS):
            return True

        return b"\x00" not in sample
