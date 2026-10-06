from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.base import Base
from app.database.engine import configure_sqlite_connections
from app.workspace.dto.workspace_create import WorkspaceCreateDTO
from app.workspace.services.workspace_service import WorkspaceService

# Register every ORM model with Base.metadata.
import app.documents.orm  # noqa: F401
import app.workspace.orm  # noqa: F401
import app.knowledge.orm  # noqa: F401

# Registers the FTS5 keyword index so create_all() creates it.
import app.knowledge.orm.keyword_index_schema  # noqa: F401


@pytest.fixture
def session() -> Generator[Session, None, None]:
    """Provide an isolated in-memory database session for a test."""

    engine = create_engine("sqlite:///:memory:")
    configure_sqlite_connections(engine)

    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        yield session

    engine.dispose()


@pytest.fixture
def workspace_id(session: Session) -> str:
    """Create a workspace and return its ID."""

    workspace = WorkspaceService(session).create_workspace(
        WorkspaceCreateDTO(name="Test Workspace")
    )

    return workspace.id
