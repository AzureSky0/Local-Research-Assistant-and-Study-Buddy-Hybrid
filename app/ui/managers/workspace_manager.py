from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject, Signal
from sqlalchemy.orm import Session

from app.database.session import create_session
from app.documents.services.document_service import DocumentService
from app.workspace.domain.workspace import Workspace
from app.workspace.dto.workspace_create import WorkspaceCreateDTO
from app.workspace.dto.workspace_update import WorkspaceUpdateDTO
from app.workspace.services.workspace_service import WorkspaceService

SessionFactory = Callable[[], Session]


class WorkspaceManager(QObject):
    """Connects workspace screens to the workspace service.

    Pages call these methods and listen to the signals; they never
    touch services or the database directly.
    """

    workspaces_changed = Signal()
    current_workspace_changed = Signal(object)  # Workspace | None

    def __init__(
        self,
        session_factory: SessionFactory = create_session,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._session_factory = session_factory
        self._current: Workspace | None = None

    @property
    def current_workspace(self) -> Workspace | None:
        return self._current

    # Queries -------------------------------------------------------------

    def list_workspaces(self) -> list[Workspace]:
        """Return active workspaces, most recently opened first."""
        with self._session_factory() as session:
            workspaces = WorkspaceService(session).list_workspaces()

        return sorted(workspaces, key=_recently_opened_first)

    def list_archived_workspaces(self) -> list[Workspace]:
        with self._session_factory() as session:
            return WorkspaceService(session).list_archived_workspaces()

    def document_counts(self) -> dict[str, int]:
        """Return the number of documents in each workspace."""
        with self._session_factory() as session:
            return DocumentService(session).get_document_counts()

    def get_workspace(self, workspace_id: str) -> Workspace | None:
        with self._session_factory() as session:
            return WorkspaceService(session).get_workspace(workspace_id)

    # Commands ------------------------------------------------------------

    def create_workspace(
        self,
        name: str,
        description: str | None,
        color: str,
    ) -> Workspace:
        with self._session_factory() as session:
            workspace = WorkspaceService(session).create_workspace(
                WorkspaceCreateDTO(
                    name=name.strip(),
                    description=_clean_optional(description),
                    color=color,
                )
            )

        self.workspaces_changed.emit()
        return workspace

    def update_workspace(
        self,
        workspace_id: str,
        name: str,
        description: str | None,
        color: str,
    ) -> Workspace | None:
        with self._session_factory() as session:
            workspace = WorkspaceService(session).update_workspace(
                workspace_id,
                WorkspaceUpdateDTO(
                    name=name.strip(),
                    description=_clean_optional(description) or "",
                    color=color,
                ),
            )

        self._after_change(workspace_id, workspace)
        return workspace

    def archive_workspace(self, workspace_id: str) -> None:
        with self._session_factory() as session:
            WorkspaceService(session).archive_workspace(workspace_id)

        if self._current is not None and self._current.id == workspace_id:
            self.close_workspace()

        self.workspaces_changed.emit()

    def restore_workspace(self, workspace_id: str) -> None:
        with self._session_factory() as session:
            WorkspaceService(session).restore_workspace(workspace_id)

        self.workspaces_changed.emit()

    def delete_workspace(self, workspace_id: str) -> None:
        """Permanently delete a workspace and its document records."""
        with self._session_factory() as session:
            WorkspaceService(session).delete_workspace(workspace_id)

        if self._current is not None and self._current.id == workspace_id:
            self.close_workspace()

        self.workspaces_changed.emit()

    def open_workspace(self, workspace_id: str) -> Workspace | None:
        """Make a workspace current and record that it was opened."""
        with self._session_factory() as session:
            workspace = WorkspaceService(session).open_workspace(workspace_id)

        self._current = workspace
        self.current_workspace_changed.emit(workspace)
        self.workspaces_changed.emit()
        return workspace

    def close_workspace(self) -> None:
        """Return to the workspaces home screen."""
        self._current = None
        self.current_workspace_changed.emit(None)

    def _after_change(self, workspace_id: str, workspace: Workspace | None) -> None:
        if (
            workspace is not None
            and self._current is not None
            and self._current.id == workspace_id
        ):
            self._current = workspace
            self.current_workspace_changed.emit(workspace)

        self.workspaces_changed.emit()


def _recently_opened_first(workspace: Workspace) -> float:
    moment = workspace.last_opened_at or workspace.created_at
    return -moment.timestamp()


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None

    value = value.strip()
    return value or None
