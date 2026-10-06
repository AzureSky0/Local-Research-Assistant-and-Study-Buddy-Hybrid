from __future__ import annotations

import codecs
from collections.abc import Iterator
from pathlib import Path

from app.documents.exceptions import ExtractionError
from app.documents.extraction.document_extractor import DocumentExtractor, ExtractedPage

TEXT_EXTRACTOR_VERSION = "text-1"

# Byte order marks identify the encoding of many Windows text files.
_BOMS: list[tuple[bytes, str]] = [
    (codecs.BOM_UTF8, "utf-8-sig"),
    (codecs.BOM_UTF16_LE, "utf-16"),
    (codecs.BOM_UTF16_BE, "utf-16"),
]

# Tried in order when there is no byte order mark. cp1252 is the usual
# encoding of older Windows files; it can decode almost any bytes.
_FALLBACK_ENCODINGS = ["utf-8", "cp1252"]


def decode_text(data: bytes) -> str:
    """Decode text bytes, detecting the encoding as well as practical."""

    for bom, encoding in _BOMS:
        if data.startswith(bom):
            return data.decode(encoding)

    for encoding in _FALLBACK_ENCODINGS:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue

    return data.decode("latin-1")


class TextExtractor(DocumentExtractor):
    """Reads plain text and Markdown files as a single page.

    Markdown is kept as written: its headings and lists are useful
    structure for search and chunking.
    """

    @property
    def file_types(self) -> frozenset[str]:
        return frozenset({"txt", "md"})

    @property
    def version(self) -> str:
        return TEXT_EXTRACTOR_VERSION

    def extract(self, file_path: Path) -> Iterator[ExtractedPage]:
        try:
            data = file_path.read_bytes()
        except FileNotFoundError as error:
            raise ExtractionError(
                "The original file is no longer at its saved location. "
                "Add it again if it has moved."
            ) from error
        except OSError as error:
            raise ExtractionError(f"The file could not be opened: {error.strerror}.") from error

        yield ExtractedPage(page_number=1, text=decode_text(data))
