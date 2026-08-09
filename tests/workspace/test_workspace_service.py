from sqlalchemy.orm import Session

from app.workspace.domain.workspace import Workspace
from app.workspace.dto.workspace_create import WorkspaceCreateDTO
from app.workspace.dto.workspace_update import WorkspaceUpdateDTO
from app.workspace.services.workspace_service import WorkspaceService


def test_create_workspace(session: Session) -> None:
    service = WorkspaceService(session)

    data = WorkspaceCreateDTO(
        name="Machine Learning",
        description="ML study materials",
        icon="brain",
        color="blue",
    )

    workspace = service.create_workspace(data)

    assert isinstance(workspace, Workspace)
    assert workspace.name == "Machine Learning"
    assert workspace.description == "ML study materials"
    assert workspace.icon == "brain"
    assert workspace.color == "blue"
    assert workspace.is_archived is False
    assert workspace.last_opened_at is None


def test_get_workspace(session: Session) -> None:
    service = WorkspaceService(session)

    workspace = service.create_workspace(
        WorkspaceCreateDTO(name="Research")
    )

    found = service.get_workspace(workspace.id)

    assert found is not None
    assert found.id == workspace.id
    assert found.name == "Research"


def test_rename_workspace(session: Session) -> None:
    service = WorkspaceService(session)

    workspace = service.create_workspace(
        WorkspaceCreateDTO(name="Old Name")
    )

    renamed = service.rename_workspace(
        workspace.id,
        "New Name",
    )

    assert renamed is not None
    assert renamed.name == "New Name"


def test_update_workspace(session: Session) -> None:
    service = WorkspaceService(session)

    workspace = service.create_workspace(
        WorkspaceCreateDTO(name="Research")
    )

    updated = service.update_workspace(
        workspace.id,
        WorkspaceUpdateDTO(
            name="AI Research",
            icon="research",
            color="green",
        ),
    )

    assert updated is not None
    assert updated.name == "AI Research"
    assert updated.icon == "research"
    assert updated.color == "green"


def test_open_workspace(session: Session) -> None:
    service = WorkspaceService(session)

    workspace = service.create_workspace(
        WorkspaceCreateDTO(name="University")
    )

    assert workspace.last_opened_at is None

    opened = service.open_workspace(workspace.id)

    assert opened is not None
    assert opened.last_opened_at is not None


def test_archive_workspace(session: Session) -> None:
    service = WorkspaceService(session)

    workspace = service.create_workspace(
        WorkspaceCreateDTO(name="Archived Workspace")
    )

    archived = service.archive_workspace(workspace.id)

    assert archived is not None
    assert archived.is_archived is True

    workspaces = service.list_workspaces()

    assert all(
        item.id != workspace.id
        for item in workspaces
    )


def test_delete_workspace(session: Session) -> None:
    service = WorkspaceService(session)

    workspace = service.create_workspace(
        WorkspaceCreateDTO(name="Temporary")
    )

    deleted = service.delete_workspace(workspace.id)

    assert deleted is True
    assert service.get_workspace(workspace.id) is None


def test_missing_workspace_operations(
    session: Session,
) -> None:
    service = WorkspaceService(session)

    workspace_id = "does-not-exist"

    assert service.get_workspace(workspace_id) is None

    assert (
        service.rename_workspace(
            workspace_id,
            "New Name",
        )
        is None
    )

    assert (
        service.update_workspace(
            workspace_id,
            WorkspaceUpdateDTO(name="New Name"),
        )
        is None
    )

    assert service.archive_workspace(workspace_id) is None

    assert service.delete_workspace(workspace_id) is False

    assert service.open_workspace(workspace_id) is None