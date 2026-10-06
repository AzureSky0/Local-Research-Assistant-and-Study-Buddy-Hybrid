from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.documents.domain import DocumentProcessingStage
from app.documents.orm import DocumentORM


class ProcessingCancelledError(Exception):
    """Raised inside a stage when processing should stop.

    The document returns to "pending" and resumes later.
    """


@dataclass(slots=True)
class ProcessingContext:
    """What a stage needs to process one document."""

    session: Session
    document: DocumentORM
    is_cancelled: Callable[[], bool]

    def check_cancelled(self) -> None:
        if self.is_cancelled():
            raise ProcessingCancelledError


class ProcessingStage(ABC):
    """One step of the document processing pipeline (Decision 031).

    A stage must be safe to run again: if processing is interrupted,
    the stage runs from the beginning next time.
    """

    @property
    @abstractmethod
    def completes(self) -> DocumentProcessingStage:
        """The stage a document has reached after this step succeeds."""

    @abstractmethod
    def run(self, context: ProcessingContext) -> None:
        """Process the document. Raise ExtractionError for user-facing failures."""
