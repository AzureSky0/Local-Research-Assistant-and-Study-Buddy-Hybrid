from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.workspace.orm import WorkspaceORM


class WorkspaceRepository:
    """Handles database persistence for workspaces."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, workspace: WorkspaceORM) -> WorkspaceORM:
        """Persist a new workspace."""
        self._session.add(workspace)
        self._session.commit()
        self._session.refresh(workspace)

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

    def update(self, workspace: WorkspaceORM) -> WorkspaceORM:
        """Persist changes to an existing workspace."""
        self._session.commit()
        self._session.refresh(workspace)

        return workspace

    def delete(self, workspace: WorkspaceORM) -> None:
        """Permanently delete a workspace."""
        self._session.delete(workspace)
        self._session.commit()

    def archive(self, workspace: WorkspaceORM) -> WorkspaceORM:
        """Archive a workspace without permanently deleting it."""
        workspace.is_archived = True
        self._session.commit()
        self._session.refresh(workspace)

        return workspace