from uuid import UUID

from sqlalchemy.orm import Session

from app.database.entities.document_entity import DocumentEntity


class DocumentRepository:

    def __init__(self, session: Session):
        self.session = session

    def create(self, entity: DocumentEntity) -> DocumentEntity:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)

        return entity

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