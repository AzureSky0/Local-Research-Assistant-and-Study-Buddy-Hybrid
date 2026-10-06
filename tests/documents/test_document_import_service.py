from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from app.documents.exceptions import (
    DocumentAlreadyImportedError,
    UnsupportedDocumentTypeError,
)
from app.documents.services.document_import_service import (
    DocumentImportService,
)
from app.documents.dto.document_import_result import (
    DocumentImportStatus,
)
from app.documents.services.document_service import DocumentService
from app.workspace.dto.workspace_create import WorkspaceCreateDTO
from app.workspace.services.workspace_service import WorkspaceService

# Minimal PDF header so test files pass content validation.
PDF_HEADER = b"%PDF-1.4\n"


def create_import_service(
    session,
) -> DocumentImportService:
    return DocumentImportService(
        document_service=DocumentService(session),
    )


def test_import_document(
    session,
    workspace_id: str,
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "example.pdf"
    content = PDF_HEADER + b"Example PDF content"

    file_path.write_bytes(content)

    service = create_import_service(session)

    document = service.import_document(workspace_id, file_path)

    assert document.workspace_id == workspace_id
    assert document.file_name == "example.pdf"
    assert document.original_path == str(file_path)
    assert document.file_size == len(content)
    assert document.file_type == "pdf"
    assert document.checksum == hashlib.sha256(
        content
    ).hexdigest()
    assert document.imported_at is not None
    assert document.id is not None


def test_import_same_file_raises_duplicate_error(
    session,
    workspace_id: str,
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "example.pdf"
    file_path.write_bytes(PDF_HEADER + b"Example PDF content")

    service = create_import_service(session)

    first_document = service.import_document(workspace_id, file_path)

    with pytest.raises(
        DocumentAlreadyImportedError
    ) as exc_info:
        service.import_document(workspace_id, file_path)

    assert (
        exc_info.value.existing_document_id
        == first_document.id
    )


def test_import_identical_content_from_different_path_raises_duplicate_error(
    session,
    workspace_id: str,
    tmp_path: Path,
) -> None:
    first_file = tmp_path / "first.pdf"
    second_file = tmp_path / "second.pdf"

    content = PDF_HEADER + b"Identical document content"

    first_file.write_bytes(content)
    second_file.write_bytes(content)

    service = create_import_service(session)

    service.import_document(workspace_id, first_file)

    with pytest.raises(
        DocumentAlreadyImportedError
    ):
        service.import_document(workspace_id, second_file)


def test_import_missing_file_raises_file_not_found_error(
    session,
    workspace_id: str,
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "missing.pdf"

    service = create_import_service(session)

    with pytest.raises(FileNotFoundError):
        service.import_document(workspace_id, file_path)


def test_import_directory_raises_value_error(
    session,
    workspace_id: str,
    tmp_path: Path,
) -> None:
    directory = tmp_path / "documents"
    directory.mkdir()

    service = create_import_service(session)

    with pytest.raises(ValueError):
        service.import_document(workspace_id, directory)


def test_import_does_not_copy_or_move_file(
    session,
    workspace_id: str,
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "example.pdf"
    file_path.write_bytes(PDF_HEADER + b"Example PDF content")

    service = create_import_service(session)

    service.import_document(workspace_id, file_path)

    assert file_path.exists()


def test_import_multiple_documents_continues_after_duplicate(
    session,
    workspace_id: str,
    tmp_path: Path,
) -> None:
    first_file = tmp_path / "first.pdf"
    duplicate_file = tmp_path / "duplicate.pdf"
    third_file = tmp_path / "third.pdf"

    first_file.write_bytes(PDF_HEADER + b"same content")
    duplicate_file.write_bytes(PDF_HEADER + b"same content")
    third_file.write_bytes(PDF_HEADER + b"different content")

    service = create_import_service(session)

    results = service.import_documents(
        workspace_id,
        [
            first_file,
            duplicate_file,
            third_file,
        ]
    )

    assert len(results) == 3

    assert (
        results[0].status
        == DocumentImportStatus.IMPORTED
    )

    assert (
        results[1].status
        == DocumentImportStatus.ALREADY_IMPORTED
    )

    assert (
        results[2].status
        == DocumentImportStatus.IMPORTED
    )


def test_import_multiple_documents_continues_after_invalid_file(
    session,
    workspace_id: str,
    tmp_path: Path,
) -> None:
    valid_file = tmp_path / "valid.pdf"
    missing_file = tmp_path / "missing.pdf"
    another_valid_file = tmp_path / "another.pdf"

    valid_file.write_bytes(PDF_HEADER + b"valid content")
    another_valid_file.write_bytes(PDF_HEADER + b"another valid content")

    service = create_import_service(session)

    results = service.import_documents(
        workspace_id,
        [
            valid_file,
            missing_file,
            another_valid_file,
        ]
    )

    assert len(results) == 3

    assert (
        results[0].status
        == DocumentImportStatus.IMPORTED
    )

    assert (
        results[1].status
        == DocumentImportStatus.FAILED
    )

    assert (
        results[2].status
        == DocumentImportStatus.IMPORTED
    )


def test_import_multiple_documents_continues_after_unreadable_file(
    session,
    workspace_id: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    unreadable_file = tmp_path / "unreadable.pdf"
    valid_file = tmp_path / "valid.pdf"

    unreadable_file.write_bytes(PDF_HEADER + b"unreadable content")
    valid_file.write_bytes(PDF_HEADER + b"valid content")

    original_checksum = DocumentImportService._calculate_checksum

    def fake_checksum(file_path: Path) -> str:
        if file_path == unreadable_file:
            raise PermissionError(
                f"Permission denied: {file_path}"
            )

        return original_checksum(file_path)

    monkeypatch.setattr(
        DocumentImportService,
        "_calculate_checksum",
        staticmethod(fake_checksum),
    )

    service = create_import_service(session)

    results = service.import_documents(
        workspace_id,
        [
            unreadable_file,
            valid_file,
        ]
    )

    assert (
        results[0].status
        == DocumentImportStatus.FAILED
    )

    assert (
        results[1].status
        == DocumentImportStatus.IMPORTED
    )


def test_same_file_can_be_imported_into_different_workspaces(
    session,
    workspace_id: str,
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "shared.pdf"
    file_path.write_bytes(PDF_HEADER + b"Shared textbook content")

    other_workspace = WorkspaceService(session).create_workspace(
        WorkspaceCreateDTO(name="Other Workspace")
    )

    service = create_import_service(session)

    first = service.import_document(workspace_id, file_path)
    second = service.import_document(other_workspace.id, file_path)

    assert first.checksum == second.checksum
    assert first.id != second.id
    assert first.workspace_id == workspace_id
    assert second.workspace_id == other_workspace.id


def test_import_unsupported_format_raises_error(
    session,
    workspace_id: str,
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "notes.docx"
    file_path.write_bytes(b"PK fake docx")

    service = create_import_service(session)

    with pytest.raises(UnsupportedDocumentTypeError) as exc_info:
        service.import_document(workspace_id, file_path)

    assert ".docx" in str(exc_info.value)
    assert "PDF" in str(exc_info.value)


def test_import_detects_file_type_case_insensitively(
    session,
    workspace_id: str,
    tmp_path: Path,
) -> None:
    pdf_file = tmp_path / "SCAN.PDF"
    markdown_file = tmp_path / "notes.markdown"

    pdf_file.write_bytes(PDF_HEADER + b"content")
    markdown_file.write_text("# Notes", encoding="utf-8")

    service = create_import_service(session)

    assert service.import_document(workspace_id, pdf_file).file_type == "pdf"
    assert service.import_document(workspace_id, markdown_file).file_type == "md"


def test_import_multiple_documents_reports_unsupported_and_invalid_files(
    session,
    workspace_id: str,
    tmp_path: Path,
) -> None:
    valid_file = tmp_path / "valid.txt"
    unsupported_file = tmp_path / "slides.pptx"
    fake_pdf = tmp_path / "fake.pdf"

    valid_file.write_text("Plain text notes", encoding="utf-8")
    unsupported_file.write_bytes(b"PK fake pptx")
    fake_pdf.write_text("Not really a PDF", encoding="utf-8")

    service = create_import_service(session)

    results = service.import_documents(
        workspace_id,
        [
            valid_file,
            unsupported_file,
            fake_pdf,
        ],
    )

    assert [result.status for result in results] == [
        DocumentImportStatus.IMPORTED,
        DocumentImportStatus.UNSUPPORTED,
        DocumentImportStatus.FAILED,
    ]
    assert results[2].error is not None
    assert "not a valid PDF" in results[2].error


def test_import_folder(
    session,
    workspace_id: str,
    tmp_path: Path,
) -> None:
    folder = tmp_path / "course"
    chapters = folder / "chapters"
    chapters.mkdir(parents=True)

    (folder / "syllabus.pdf").write_bytes(PDF_HEADER + b"syllabus")
    (chapters / "chapter1.md").write_text("# Chapter 1", encoding="utf-8")
    (folder / "slides.pptx").write_bytes(b"PK fake pptx")
    (folder / ".hidden.txt").write_text("hidden", encoding="utf-8")

    service = create_import_service(session)

    results = service.import_folder(workspace_id, folder)

    statuses = {
        Path(result.file_path).name: result.status
        for result in results
    }

    assert statuses == {
        "chapter1.md": DocumentImportStatus.IMPORTED,
        "syllabus.pdf": DocumentImportStatus.IMPORTED,
        "slides.pptx": DocumentImportStatus.UNSUPPORTED,
    }


def test_import_folder_twice_reports_duplicates(
    session,
    workspace_id: str,
    tmp_path: Path,
) -> None:
    folder = tmp_path / "papers"
    folder.mkdir()
    (folder / "paper.pdf").write_bytes(PDF_HEADER + b"paper")

    service = create_import_service(session)

    service.import_folder(workspace_id, folder)
    results = service.import_folder(workspace_id, folder)

    assert [result.status for result in results] == [
        DocumentImportStatus.ALREADY_IMPORTED,
    ]

