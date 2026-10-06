from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.workspace.orm import WorkspaceORM


class WorkspaceRepository:
    """Handles database persistence for workspaces.

    The repository never commits. Transaction boundaries belong
    to the service layer.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, workspace: WorkspaceORM) -> WorkspaceORM:
        """Stage a new workspace and flush it to the database."""
        self._session.add(workspace)
        self._session.flush()

        return workspace

    def get_by_id(self, workspace_id: str) -> WorkspaceORM | None:
        """Return a workspace by its primary key."""
        return self._session.get(
            WorkspaceORM,
            workspace_id,
        )

    def get_all(self) -> list[WorkspaceORM]:
        """Return all active workspaces ordered by name."""
        statement = (
            select(WorkspaceORM)
            .where(WorkspaceORM.is_archived.is_(False))
            .order_by(WorkspaceORM.name)
        )

        return list(
            self._session.scalars(statement)
        )

    def get_archived(self) -> list[WorkspaceORM]:
        """Return all archived workspaces ordered by name."""
        statement = (
            select(WorkspaceORM)
            .where(WorkspaceORM.is_archived.is_(True))
            .order_by(WorkspaceORM.name)
        )

        return list(
            self._session.scalars(statement)
        )

    def delete(self, workspace: WorkspaceORM) -> None:
        """Stage permanent deletion of a workspace."""
        self._session.delete(workspace)
        self._session.flush()
