from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ExtractedPage:
    """Raw text of one page, numbered from 1."""

    page_number: int
    text: str


class DocumentExtractor(ABC):
    """Reads the text of one kind of document (Decision 028).

    Extractors yield pages one at a time so large documents are never
    held in memory all at once (NFR-PERF-005). They raise
    ExtractionError with a user-friendly message when a file cannot
    be read.
    """

    @property
    @abstractmethod
    def file_types(self) -> frozenset[str]:
        """Document file types this extractor reads, for example {"pdf"}."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Changes whenever the extracted text for the same file would change."""

    @abstractmethod
    def extract(self, file_path: Path) -> Iterator[ExtractedPage]:
        """Yield the pages of a document in order."""


def read_capability(file_type: str) -> str:
    """Capability name for reading a file type, for example document.pdf.read."""
    return f"document.{file_type}.read"
