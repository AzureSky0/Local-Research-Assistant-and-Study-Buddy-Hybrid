from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.base import Base


@pytest.fixture
def session() -> Generator[Session, None, None]:
    """Provide an isolated in-memory database session for a test."""

    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        yield session

    engine.dispose()