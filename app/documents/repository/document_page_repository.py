from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.documents.orm import DocumentORM, DocumentPageORM

COPY_BATCH_SIZE = 200


class DocumentPageRepository:
    """Handles persistence of extracted page text.

    The repository never commits. Transaction boundaries belong
    to the service layer.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def add_pages(self, document_id: str, pages: Iterable[tuple[int, str]]) -> int:
        """Stage pages given as (page number, text). Returns how many were added."""
        count = 0

        for page_number, text in pages:
            self._session.add(
                DocumentPageORM(
                    document_id=document_id,
                    page_number=page_number,
                    text=text,
                )
            )
            count += 1

        self._session.flush()
        return count

    def delete_for_document(self, document_id: str) -> None:
        """Remove all pages of a document (before extracting it again)."""
        self._session.execute(
            delete(DocumentPageORM).where(DocumentPageORM.document_id == document_id)
        )

    def list_for_document(self, document_id: str) -> list[DocumentPageORM]:
        statement = (
            select(DocumentPageORM)
            .where(DocumentPageORM.document_id == document_id)
            .order_by(DocumentPageORM.page_number)
        )

        return list(self._session.scalars(statement))

    def count_for_document(self, document_id: str) -> int:
        statement = select(func.count(DocumentPageORM.id)).where(
            DocumentPageORM.document_id == document_id
        )

        return int(self._session.scalar(statement) or 0)

    def find_reusable_source(
        self,
        checksum: str,
        extractor_version: str,
        exclude_document_id: str,
    ) -> str | None:
        """Return a document whose extracted text can be reused.

        Identical content (same checksum) extracted with the same
        extractor version produces identical pages (Decision 031).
        """
        statement = (
            select(DocumentORM.id)
            .where(
                DocumentORM.checksum == checksum,
                DocumentORM.extractor_version == extractor_version,
                DocumentORM.page_count.is_not(None),
                DocumentORM.id != exclude_document_id,
            )
            .limit(1)
        )

        return self._session.scalar(statement)

    def copy_pages(self, source_document_id: str, target_document_id: str) -> int:
        """Copy all pages of one document to another. Returns the page count."""
        statement = (
            select(DocumentPageORM.page_number, DocumentPageORM.text)
            .where(DocumentPageORM.document_id == source_document_id)
            .order_by(DocumentPageORM.page_number)
            .execution_options(yield_per=COPY_BATCH_SIZE)
        )

        rows = list(self._session.execute(statement))
        return self.add_pages(target_document_id, ((row[0], row[1]) for row in rows))
