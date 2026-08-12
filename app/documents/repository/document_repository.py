from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.documents.orm import DocumentORM


class DocumentRepository:
    """Handles database persistence for documents."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, document: DocumentORM) -> DocumentORM:
        """Persist a new document."""
        self._session.add(document)
        self._session.commit()
        self._session.refresh(document)

        return document

    def get_by_id(self, document_id: str) -> DocumentORM | None:
        """Return a document by its primary key."""
        return self._session.get(
            DocumentORM,
            document_id,
        )

    def get_by_checksum(
        self,
        checksum: str,
    ) -> DocumentORM | None:
        """Return a document matching the given checksum."""
        statement = select(DocumentORM).where(
            DocumentORM.checksum == checksum
        )

        return self._session.scalars(
            statement
        ).first()

    def get_all(self) -> list[DocumentORM]:
        """Return all documents."""
        statement = select(DocumentORM)

        return list(
            self._session.scalars(statement)
        )