from __future__ import annotations

from collections.abc import Collection

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.documents.domain import DocumentProcessingStage, DocumentProcessingStatus
from app.documents.orm import DocumentORM


class DocumentRepository:
    """Handles database persistence for documents.

    The repository never commits. Transaction boundaries belong
    to the service layer.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, document: DocumentORM) -> DocumentORM:
        """Stage a new document and flush it to the database."""
        self._session.add(document)
        self._session.flush()

        return document

    def get_by_id(self, document_id: str) -> DocumentORM | None:
        """Return a document by its primary key."""
        return self._session.get(
            DocumentORM,
            document_id,
        )

    def get_by_checksum(
        self,
        workspace_id: str,
        checksum: str,
    ) -> DocumentORM | None:
        """Return the workspace document matching the given checksum."""
        statement = select(DocumentORM).where(
            DocumentORM.workspace_id == workspace_id,
            DocumentORM.checksum == checksum,
        )

        return self._session.scalars(
            statement
        ).first()

    def list_by_workspace(
        self,
        workspace_id: str,
    ) -> list[DocumentORM]:
        """Return all documents in a workspace, oldest import first."""
        statement = (
            select(DocumentORM)
            .where(DocumentORM.workspace_id == workspace_id)
            .order_by(DocumentORM.imported_at)
        )

        return list(
            self._session.scalars(statement)
        )

    def count_by_workspace(self) -> dict[str, int]:
        """Return the number of documents in each workspace."""
        statement = select(
            DocumentORM.workspace_id,
            func.count(DocumentORM.id),
        ).group_by(DocumentORM.workspace_id)

        return {
            workspace_id: count
            for workspace_id, count in self._session.execute(statement)
        }

    def delete(self, document: DocumentORM) -> None:
        """Stage removal of a document record."""
        self._session.delete(document)
        self._session.flush()

    def next_pending_id(self, exclude: Collection[str] = ()) -> str | None:
        """Return the next document waiting to be processed.

        Smaller files go first so they become available sooner
        (Decision 031).
        """
        statement = (
            select(DocumentORM.id)
            .where(DocumentORM.processing_status == DocumentProcessingStatus.PENDING)
            .order_by(DocumentORM.file_size, DocumentORM.imported_at)
            .limit(1)
        )

        if exclude:
            statement = statement.where(DocumentORM.id.not_in(list(exclude)))

        return self._session.scalar(statement)

    def count_with_status(self, status: DocumentProcessingStatus) -> int:
        statement = select(func.count(DocumentORM.id)).where(
            DocumentORM.processing_status == status
        )

        return int(self._session.scalar(statement) or 0)

    def requeue_interrupted(self) -> int:
        """Mark documents left "processing" by a previous run as pending."""
        result = self._session.execute(
            update(DocumentORM)
            .where(DocumentORM.processing_status == DocumentProcessingStatus.PROCESSING)
            .values(processing_status=DocumentProcessingStatus.PENDING)
        )

        return int(result.rowcount or 0)  # type: ignore[attr-defined]

    def requeue_unfinished(self, completed_stages: Collection[DocumentProcessingStage]) -> int:
        """Mark ready documents that have not completed every stage as pending.

        Happens when a new version adds processing stages.
        """
        result = self._session.execute(
            update(DocumentORM)
            .where(
                DocumentORM.processing_status == DocumentProcessingStatus.READY,
                DocumentORM.processed_stage.not_in(list(completed_stages)),
            )
            .values(processing_status=DocumentProcessingStatus.PENDING)
        )

        return int(result.rowcount or 0)  # type: ignore[attr-defined]

    def search_by_name(
        self,
        workspace_id: str,
        text: str,
        limit: int,
    ) -> list[DocumentORM]:
        """Documents whose file name contains the text (case-insensitive)."""
        # Treat % and _ typed by the user as literal characters.
        escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

        statement = (
            select(DocumentORM)
            .where(
                DocumentORM.workspace_id == workspace_id,
                DocumentORM.file_name.ilike(f"%{escaped}%", escape="\\"),
            )
            .order_by(DocumentORM.file_name)
            .limit(limit)
        )

        return list(self._session.scalars(statement))
