from __future__ import annotations

import logging
from pathlib import Path

from app.database.transaction import commit
from app.documents.domain import DocumentProcessingStage
from app.documents.exceptions import ExtractionError
from app.documents.extraction.document_extractor import DocumentExtractor
from app.documents.extraction.extractor_registry import ExtractorRegistry
from app.documents.extraction.text_normalizer import NORMALIZER_VERSION, normalize_text
from app.documents.processing.processing_stage import ProcessingContext, ProcessingStage
from app.documents.repository.document_page_repository import DocumentPageRepository

logger = logging.getLogger(__name__)

# Pages are written in batches so a long book never holds the
# database write lock for long while imports also write.
PAGE_BATCH_SIZE = 50

NO_TEXT_IN_PDF = (
    "No text was found. This looks like a scanned document or a file made of "
    "images. Reading scanned pages (OCR) will come as an extension."
)
NO_TEXT_IN_FILE = "The file contains no text."


def extraction_version(extractor: DocumentExtractor) -> str:
    """Cache key for extracted text: extractor and normalizer versions."""
    return f"{extractor.version}+norm-{NORMALIZER_VERSION}"


class ExtractTextStage(ProcessingStage):
    """Reads a document's text and stores it page by page."""

    def __init__(self, extractors: ExtractorRegistry) -> None:
        self._extractors = extractors

    @property
    def completes(self) -> DocumentProcessingStage:
        return DocumentProcessingStage.EXTRACTED

    def run(self, context: ProcessingContext) -> None:
        document = context.document
        pages = DocumentPageRepository(context.session)

        extractor = self._extractors.extractor_for(document.file_type)
        version = extraction_version(extractor)

        # Start clean: an interrupted earlier attempt may have left pages.
        pages.delete_for_document(document.id)

        source_id = pages.find_reusable_source(document.checksum, version, document.id)

        if source_id is not None:
            logger.info("Reusing extracted text of %s for %s", source_id, document.id)
            page_count = pages.copy_pages(source_id, document.id)
        else:
            page_count = self._extract(context, extractor, pages)

        document.page_count = page_count
        document.extractor_version = version

    def _extract(
        self,
        context: ProcessingContext,
        extractor: DocumentExtractor,
        pages: DocumentPageRepository,
    ) -> int:
        document = context.document

        page_count = 0
        character_count = 0
        batch: list[tuple[int, str]] = []

        for page in extractor.extract(Path(document.original_path)):
            context.check_cancelled()

            text = normalize_text(page.text)
            character_count += len(text)
            page_count += 1
            batch.append((page.page_number, text))

            if len(batch) >= PAGE_BATCH_SIZE:
                pages.add_pages(document.id, batch)
                commit(context.session)
                batch = []

        if batch:
            pages.add_pages(document.id, batch)

        if character_count == 0:
            raise ExtractionError(
                NO_TEXT_IN_PDF if document.file_type == "pdf" else NO_TEXT_IN_FILE
            )

        return page_count
