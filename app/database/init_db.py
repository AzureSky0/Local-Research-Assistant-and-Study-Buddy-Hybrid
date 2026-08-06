from app.database.base import Base
from app.database.engine import engine

# Import entities so SQLAlchemy registers them
from app.documents.orm.document_orm import DocumentORM


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)