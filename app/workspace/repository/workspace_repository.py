from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.workspace.orm.workspace_orm import WorkspaceORM


class WorkspaceRepository:
    """Handles persistence for Workspace entities."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, workspace: WorkspaceORM) -> WorkspaceORM:
        self._session.add(workspace)
        self._session.commit()
        self._session.refresh(workspace)
        return workspace

    def get_by_id(self, workspace_id: str) -> WorkspaceORM | None:
        return self._session.get(WorkspaceORM, workspace_id)

    def get_all(self) -> list[WorkspaceORM]:
        statement = (
            select(WorkspaceORM)
            .where(WorkspaceORM.is_archived.is_(False))
            .order_by(WorkspaceORM.name)
        )

        return list(self._session.scalars(statement))

    def update(self, workspace: WorkspaceORM) -> WorkspaceORM:
        self._session.commit()
        self._session.refresh(workspace)
        return workspace

    def delete(self, workspace: WorkspaceORM) -> None:
        self._session.delete(workspace)
        self._session.commit()

    def archive(self, workspace: WorkspaceORM) -> WorkspaceORM:
        workspace.is_archived = True
        self._session.commit()
        self._session.refresh(workspace)
        return workspace