from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.workspace.domain.workspace import Workspace
from app.workspace.dto.workspace_create import WorkspaceCreateDTO
from app.workspace.dto.workspace_update import WorkspaceUpdateDTO
from app.workspace.mapper.workspace_mapper import WorkspaceMapper
from app.workspace.repository.workspace_repository import WorkspaceRepository


class WorkspaceService:
    """Provides business operations for workspaces."""

    def __init__(self, session: Session) -> None:
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

        saved_workspace = self._repository.create(
            workspace_orm
        )

        return WorkspaceMapper.to_domain(
            saved_workspace
        )

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

        saved_workspace = self._repository.update(
            workspace_orm
        )

        return WorkspaceMapper.to_domain(
            saved_workspace
        )

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

        saved_workspace = self._repository.update(
            workspace_orm
        )

        return WorkspaceMapper.to_domain(
            saved_workspace
        )

    def archive_workspace(
        self,
        workspace_id: str,
    ) -> Workspace | None:
        """Archive an existing workspace."""

        workspace_orm = self._repository.get_by_id(
            workspace_id
        )

        if workspace_orm is None:
            return None

        archived_workspace = self._repository.archive(
            workspace_orm
        )

        return WorkspaceMapper.to_domain(
            archived_workspace
        )

    def delete_workspace(
        self,
        workspace_id: str,
    ) -> bool:
        """Permanently delete an existing workspace."""

        workspace_orm = self._repository.get_by_id(
            workspace_id
        )

        if workspace_orm is None:
            return False

        self._repository.delete(workspace_orm)

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

        saved_workspace = self._repository.update(
            workspace_orm
        )

        return WorkspaceMapper.to_domain(
            saved_workspace
        )

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

        workspaces_orm = self._repository.get_all()

        return [
            WorkspaceMapper.to_domain(
                workspace_orm
            )
            for workspace_orm in workspaces_orm
        ]