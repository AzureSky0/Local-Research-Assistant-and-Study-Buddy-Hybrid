from __future__ import annotations

from app.documents.domain import DocumentProcessingStage
from app.documents.processing.processing_stage import ProcessingContext, ProcessingStage
from app.documents.repository.document_page_repository import DocumentPageRepository
from app.knowledge.services.chunking_service import ChunkingService


class ChunkStage(ProcessingStage):
    """Splits a document's pages into retrievable chunks (Decision 031).

    Chunks belong to the Knowledge subsystem; this stage passes it the
    pages the extraction stage stored.
    """

    @property
    def completes(self) -> DocumentProcessingStage:
        return DocumentProcessingStage.CHUNKED

    def run(self, context: ProcessingContext) -> None:
        context.check_cancelled()

        pages = DocumentPageRepository(context.session).list_for_document(context.document.id)

        ChunkingService(context.session).chunk_document(
            context.document.id,
            ((page.page_number, page.text) for page in pages),
        )
