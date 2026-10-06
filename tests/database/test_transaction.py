from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.transaction import commit
from app.workspace.orm import WorkspaceORM


def create_workspace_orm(workspace_id: str) -> WorkspaceORM:
    now = datetime.now(UTC)

    return WorkspaceORM(
        id=workspace_id,
        name="Workspace",
        icon="folder",
        color="blue",
        created_at=now,
        updated_at=now,
        is_archived=False,
    )


def test_failed_commit_is_rolled_back(session: Session) -> None:
    session.add(create_workspace_orm("same-id"))
    commit(session)

    session.add(create_workspace_orm("same-id"))

    with pytest.raises(IntegrityError):
        commit(session)

    # The session is usable again after the rollback.
    session.add(create_workspace_orm("another-id"))
    commit(session)

    assert session.get(WorkspaceORM, "another-id") is not None


def test_file_database_uses_wal_and_foreign_keys(tmp_path) -> None:
    from sqlalchemy import create_engine, text

    from app.database.engine import configure_sqlite_connections

    engine = create_engine(f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    configure_sqlite_connections(engine)

    with engine.connect() as connection:
        assert connection.execute(text("PRAGMA journal_mode")).scalar() == "wal"
        assert connection.execute(text("PRAGMA foreign_keys")).scalar() == 1

    engine.dispose()
