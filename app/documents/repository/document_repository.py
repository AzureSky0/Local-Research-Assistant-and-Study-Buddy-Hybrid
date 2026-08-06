from uuid import UUID

from sqlalchemy.orm import Session

from app.documents.orm.document_orm import DocumentEntity


class DocumentRepository:

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        document: DocumentEntity,
    ) -> DocumentEntity:

        self.session.add(document)
        self.session.commit()
        self.session.refresh(document)

        return document

    def get_by_id(
        self,
        document_id: UUID,
    ) -> DocumentEntity | None:

        return (
            self.session.query(DocumentEntity)
            .filter(
                DocumentEntity.id == str(document_id)
            )
            .first()
        )

    def get_all(self) -> list[DocumentEntity]:
        return (
            self.session.query(DocumentEntity)
            .all()
        )