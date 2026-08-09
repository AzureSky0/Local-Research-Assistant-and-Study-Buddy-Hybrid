from app.workspace.domain.workspace import Workspace
from app.workspace.orm.workspace_orm import WorkspaceORM


class WorkspaceMapper:

    @staticmethod
    def to_orm(workspace: Workspace) -> WorkspaceORM:
        return WorkspaceORM(
            id=workspace.id,
            name=workspace.name,
            description=workspace.description,
            icon=workspace.icon,
            color=workspace.color,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
            last_opened_at=workspace.last_opened_at,
            is_archived=workspace.is_archived,
        )

    @staticmethod
    def to_domain(entity: WorkspaceORM) -> Workspace:
        return Workspace(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            icon=entity.icon,
            color=entity.color,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            last_opened_at=entity.last_opened_at,
            is_archived=entity.is_archived,
        )