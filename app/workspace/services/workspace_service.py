from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.database.transaction import commit
from app.workspace.domain.workspace import Workspace
from app.workspace.dto.workspace_create import WorkspaceCreateDTO
from app.workspace.dto.workspace_update import WorkspaceUpdateDTO
from app.workspace.mapper.workspace_mapper import WorkspaceMapper
from app.workspace.orm import WorkspaceORM
from app.workspace.repository.workspace_repository import WorkspaceRepository


class WorkspaceService:
    """Provides business operations for workspaces."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._repository = WorkspaceRepository(session)

    def create_workspace(
        self,
        data: WorkspaceCreateDTO,
    ) -> Workspace:
        """Create and persist a new workspace."""

        now = datetime.now(UTC)

        workspace = Workspace(
            id=str(uuid4()),
            name=data.name,
            description=data.description,
            icon=data.icon,
            color=data.color,
            created_at=now,
            updated_at=now,
            last_opened_at=None,
            is_archived=False,
        )

        workspace_orm = WorkspaceMapper.to_orm(
            workspace
        )

        self._repository.add(workspace_orm)

        return self._save(workspace_orm)

    def rename_workspace(
        self,
        workspace_id: str,
        name: str,
    ) -> Workspace | None:
        """Rename an existing workspace."""

        workspace_orm = self._repository.get_by_id(
            workspace_id
        )

        if workspace_orm is None:
            return None

        workspace_orm.name = name

        return self._save(workspace_orm)

    def update_workspace(
        self,
        workspace_id: str,
        data: WorkspaceUpdateDTO,
    ) -> Workspace | None:
        """Update editable workspace fields."""

        workspace_orm = self._repository.get_by_id(
            workspace_id
        )

        if workspace_orm is None:
            return None

        if data.name is not None:
            workspace_orm.name = data.name

        if data.description is not None:
            workspace_orm.description = data.description

        if data.icon is not None:
            workspace_orm.icon = data.icon

        if data.color is not None:
            workspace_orm.color = data.color

        if data.is_archived is not None:
            workspace_orm.is_archived = data.is_archived

        return self._save(workspace_orm)

    def archive_workspace(
        self,
        workspace_id: str,
    ) -> Workspace | None:
        """Archive an existing workspace."""

        return self._set_archived(workspace_id, True)

    def restore_workspace(
        self,
        workspace_id: str,
    ) -> Workspace | None:
        """Restore an archived workspace."""

        return self._set_archived(workspace_id, False)

    def delete_workspace(
        self,
        workspace_id: str,
    ) -> bool:
        """Permanently delete a workspace and its document records.

        The user's original source files are never touched.
        """

        workspace_orm = self._repository.get_by_id(
            workspace_id
        )

        if workspace_orm is None:
            return False

        self._repository.delete(workspace_orm)
        commit(self._session)

        return True

    def open_workspace(
        self,
        workspace_id: str,
    ) -> Workspace | None:
        """Mark a workspace as recently opened."""

        workspace_orm = self._repository.get_by_id(
            workspace_id
        )

        if workspace_orm is None:
            return None

        workspace_orm.last_opened_at = datetime.now(UTC)

        return self._save(workspace_orm)

    def get_workspace(
        self,
        workspace_id: str,
    ) -> Workspace | None:
        """Return a workspace by ID."""

        workspace_orm = self._repository.get_by_id(
            workspace_id
        )

        if workspace_orm is None:
            return None

        return WorkspaceMapper.to_domain(
            workspace_orm
        )

    def list_workspaces(self) -> list[Workspace]:
        """Return all active workspaces."""

        return [
            WorkspaceMapper.to_domain(workspace_orm)
            for workspace_orm in self._repository.get_all()
        ]

    def list_archived_workspaces(self) -> list[Workspace]:
        """Return all archived workspaces."""

        return [
            WorkspaceMapper.to_domain(workspace_orm)
            for workspace_orm in self._repository.get_archived()
        ]

    def _set_archived(
        self,
        workspace_id: str,
        is_archived: bool,
    ) -> Workspace | None:
        """Change the archive state of a workspace."""

        workspace_orm = self._repository.get_by_id(
            workspace_id
        )

        if workspace_orm is None:
            return None

        workspace_orm.is_archived = is_archived

        return self._save(workspace_orm)

    def _save(self, workspace_orm: WorkspaceORM) -> Workspace:
        """Commit pending changes and return the saved workspace."""

        commit(self._session)

        return WorkspaceMapper.to_domain(
            workspace_orm
        )
