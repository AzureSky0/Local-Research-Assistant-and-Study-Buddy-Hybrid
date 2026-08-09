from sqlalchemy.orm import sessionmaker, Session

from app.database.engine import engine

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

def create_session() -> Session:
    return SessionLocal()