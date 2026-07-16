from sqlalchemy.orm import Session

from app.database.session import SessionLocal


def get_session() -> Session:
    return SessionLocal()