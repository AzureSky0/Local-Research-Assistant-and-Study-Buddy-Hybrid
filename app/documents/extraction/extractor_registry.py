from __future__ import annotations

from app.core.capabilities import CapabilityNotAvailableError, CapabilityRegistry
from app.documents.exceptions import ExtractionError
from app.documents.extraction.document_extractor import DocumentExtractor, read_capability
from app.documents.extraction.pdf_extractor import PdfExtractor
from app.documents.extraction.text_extractor import TextExtractor


class ExtractorRegistry:
    """Finds the extractor for a file type through the capability registry."""

    def __init__(self, registry: CapabilityRegistry[DocumentExtractor] | None = None) -> None:
        self._registry: CapabilityRegistry[DocumentExtractor] = registry or CapabilityRegistry()

    def register(self, extractor: DocumentExtractor) -> None:
        for file_type in extractor.file_types:
            self._registry.register(read_capability(file_type), extractor)

    def extractor_for(self, file_type: str) -> DocumentExtractor:
        try:
            return self._registry.get(read_capability(file_type))
        except CapabilityNotAvailableError as error:
            raise ExtractionError(
                f"Reading .{file_type} files is not available yet. "
                "It may come as an extension."
            ) from error


def default_extractor_registry() -> ExtractorRegistry:
    """The built-in readers, registered like any future extension."""

    registry = ExtractorRegistry()
    registry.register(PdfExtractor())
    registry.register(TextExtractor())
    return registry
