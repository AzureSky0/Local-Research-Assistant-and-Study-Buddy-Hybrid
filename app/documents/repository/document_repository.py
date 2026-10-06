from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

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

