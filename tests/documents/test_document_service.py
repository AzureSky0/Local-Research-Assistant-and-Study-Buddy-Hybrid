from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.documents.domain import (
    Document,
    DocumentProcessingStatus,
)
from app.documents.services.document_service import DocumentService
from app.workspace.dto.workspace_create import WorkspaceCreateDTO
from app.workspace.services.workspace_service import WorkspaceService


def create_document(
    workspace_id: str,
    document_id: str = "test-document-id",
    checksum: str = "test-checksum",
) -> Document:
    return Document(
        id=document_id,
        workspace_id=workspace_id,
        file_name="example.pdf",
        original_path=r"D:\Temp\example.pdf",
        file_size=1024,
        checksum=checksum,
        file_type="pdf",
        imported_at=datetime.now(UTC),
        processing_status=DocumentProcessingStatus.PENDING,
    )


def test_create_and_get_document(
    session: Session,
    workspace_id: str,
) -> None:
    service = DocumentService(session)

    document = create_document(workspace_id)

    saved = service.create_document(document)

    assert saved.id == document.id
    assert saved.workspace_id == workspace_id
    assert saved.file_name == "example.pdf"
    assert saved.original_path == r"D:\Temp\example.pdf"
    assert saved.file_size == 1024
    assert saved.checksum == "test-checksum"
    assert saved.file_type == "pdf"

    documents = service.get_documents(workspace_id)

    assert len(documents) == 1
    assert documents[0].id == document.id


def test_documents_are_isolated_by_workspace(
    session: Session,
    workspace_id: str,
) -> None:
    other_workspace = WorkspaceService(session).create_workspace(
        WorkspaceCreateDTO(name="Other Workspace")
    )

    service = DocumentService(session)

    service.create_document(create_document(workspace_id, "doc-1", "checksum-1"))
    service.create_document(create_document(other_workspace.id, "doc-2", "checksum-2"))

    assert [d.id for d in service.get_documents(workspace_id)] == ["doc-1"]
    assert [d.id for d in service.get_documents(other_workspace.id)] == ["doc-2"]


def test_find_by_checksum_is_scoped_to_workspace(
    session: Session,
    workspace_id: str,
) -> None:
    other_workspace = WorkspaceService(session).create_workspace(
        WorkspaceCreateDTO(name="Other Workspace")
    )

    service = DocumentService(session)
    service.create_document(create_document(workspace_id))

    assert service.find_by_checksum(workspace_id, "test-checksum") is not None
    assert service.find_by_checksum(other_workspace.id, "test-checksum") is None


def test_imported_at_is_timezone_aware_utc(
    session: Session,
    workspace_id: str,
) -> None:
    service = DocumentService(session)
    service.create_document(create_document(workspace_id))

    session.expire_all()

    document = service.get_documents(workspace_id)[0]

    assert document.imported_at.tzinfo is UTC
