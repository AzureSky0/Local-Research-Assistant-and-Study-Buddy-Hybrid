from app.repositories.document_repository import (
    DocumentRepository,
)
from app.database.session import get_session


class DocumentService:

    def __init__(self):
        self.session = get_session()
        self.repository = DocumentRepository(
            self.session
        )