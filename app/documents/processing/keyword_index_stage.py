from __future__ import annotations

from app.documents.domain import DocumentProcessingStage
from app.documents.processing.processing_stage import ProcessingContext, ProcessingStage
from app.knowledge.services.keyword_search_service import KeywordSearchService


class KeywordIndexStage(ProcessingStage):
    """Adds a document's pages to the keyword search index (Decision 031).

    The index belongs to the Knowledge subsystem; this stage only asks
    it to index the pages the extraction stage stored.
    """

    @property
    def completes(self) -> DocumentProcessingStage:
        return DocumentProcessingStage.KEYWORD_INDEXED

    def run(self, context: ProcessingContext) -> None:
        context.check_cancelled()
        KeywordSearchService(context.session).index_document(context.document.id)
