from __future__ import annotations

import logging
from collections.abc import Callable, Collection, Sequence

from sqlalchemy.orm import Session

from app.database.transaction import commit
from app.documents.domain import (
    Document,
    DocumentProcessingStage,
    DocumentProcessingStatus,
)
from app.documents.domain.document_processing_stage import stage_index
from app.documents.exceptions import ExtractionError
from app.documents.extraction.extractor_registry import default_extractor_registry
from app.documents.mapper.document_mapper import DocumentMapper
from app.documents.processing.chunk_stage import ChunkStage
from app.documents.processing.extract_text_stage import ExtractTextStage
from app.documents.processing.keyword_index_stage import KeywordIndexStage
from app.documents.processing.processing_stage import (
    ProcessingCancelledError,
    ProcessingContext,
    ProcessingStage,
)
from app.documents.repository.document_page_repository import DocumentPageRepository
from app.documents.repository.document_repository import DocumentRepository

logger = logging.getLogger(__name__)

UNEXPECTED_ERROR = (
    "Something went wrong while reading this document. Try again; if it keeps "
    "happening, the log file (Settings › Logs) has the details."
)

DocumentCallback = Callable[[Document], None]


def default_stages() -> list[ProcessingStage]:
    """The processing pipeline, in order."""
    return [
        ExtractTextStage(default_extractor_registry()),
        KeywordIndexStage(),
        ChunkStage(),
    ]


class DocumentProcessingService:
    """Runs the processing pipeline for documents (Decision 031).

    Each document moves through the stages in order. Progress is saved
    after every stage, so an interrupted document resumes where it
    stopped. Failures are recorded with a user-facing reason.
    """

    def __init__(
        self,
        session: Session,
        stages: Sequence[ProcessingStage] | None = None,
    ) -> None:
        self._session = session
        self._documents = DocumentRepository(session)
        self._pages = DocumentPageRepository(session)
        self._stages = list(stages) if stages is not None else default_stages()

    @property
    def final_stage(self) -> DocumentProcessingStage:
        return self._stages[-1].completes

    # Queue -------------------------------------------------------------------

    def recover(self) -> int:
        """Prepare the queue at start-up. Returns how many documents were requeued.

        Documents interrupted mid-processing, and documents that have
        not completed stages added by a newer version, become pending.
        """
        completed = [
            stage
            for stage in DocumentProcessingStage
            if stage_index(stage) >= stage_index(self.final_stage)
        ]

        count = self._documents.requeue_interrupted()
        count += self._documents.requeue_unfinished(completed)
        commit(self._session)
        return count

    def next_document_id(self, exclude: Collection[str] = ()) -> str | None:
        return self._documents.next_pending_id(exclude)

    def pending_count(self) -> int:
        return self._documents.count_with_status(DocumentProcessingStatus.PENDING)

    # Processing ----------------------------------------------------------------

    def process(
        self,
        document_id: str,
        is_cancelled: Callable[[], bool] = lambda: False,
        on_started: DocumentCallback | None = None,
    ) -> Document | None:
        """Run the remaining stages for one pending document.

        Returns the updated document, or None if it no longer exists
        or was not pending. Raises ProcessingCancelledError when
        cancelled; the document is then pending again.
        """

        document = self._documents.get_by_id(document_id)

        if document is None or document.processing_status is not DocumentProcessingStatus.PENDING:
            return None

        document.processing_status = DocumentProcessingStatus.PROCESSING
        document.processing_error = None
        commit(self._session)

        if on_started is not None:
            on_started(DocumentMapper.to_domain(document))

        try:
            for stage in self._remaining_stages(document.processed_stage):
                stage.run(ProcessingContext(self._session, document, is_cancelled))
                document.processed_stage = stage.completes
                commit(self._session)

            document.processing_status = DocumentProcessingStatus.READY
            commit(self._session)

        except ProcessingCancelledError:
            self._session.rollback()
            self._finish(document_id, DocumentProcessingStatus.PENDING, None)
            raise

        except ExtractionError as error:
            self._session.rollback()
            logger.info("Could not read document %s: %s", document_id, error)
            return self._finish(document_id, DocumentProcessingStatus.FAILED, str(error))

        except Exception:
            self._session.rollback()
            logger.exception("Unexpected error while processing document %s", document_id)
            return self._finish(document_id, DocumentProcessingStatus.FAILED, UNEXPECTED_ERROR)

        return DocumentMapper.to_domain(document)

    def retry(self, document_id: str) -> Document | None:
        """Queue a failed or stopped document for processing again (FR-KN-006)."""

        document = self._documents.get_by_id(document_id)

        if document is None or document.processing_status not in (
            DocumentProcessingStatus.FAILED,
            DocumentProcessingStatus.CANCELLED,
        ):
            return None

        document.processing_status = DocumentProcessingStatus.PENDING
        document.processing_error = None
        commit(self._session)

        return DocumentMapper.to_domain(document)

    # Internals -------------------------------------------------------------------

    def _remaining_stages(self, completed: DocumentProcessingStage) -> list[ProcessingStage]:
        return [
            stage
            for stage in self._stages
            if stage_index(stage.completes) > stage_index(completed)
        ]

    def _finish(
        self,
        document_id: str,
        status: DocumentProcessingStatus,
        error: str | None,
    ) -> Document | None:
        """Record the outcome after a rollback. The document may have been deleted."""

        document = self._documents.get_by_id(document_id)

        if document is None:
            return None

        # Text from a failed or interrupted extraction is incomplete.
        if stage_index(document.processed_stage) < stage_index(DocumentProcessingStage.EXTRACTED):
            self._pages.delete_for_document(document_id)
            document.page_count = None

        document.processing_status = status
        document.processing_error = error
        commit(self._session)

        return DocumentMapper.to_domain(document)
