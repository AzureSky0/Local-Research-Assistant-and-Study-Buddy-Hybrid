from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from app.documents.exceptions import DocumentAlreadyImportedError
from app.documents.repository.document_repository import DocumentRepository
from app.documents.services.document_import_service import (
    DocumentImportService,
)
from app.documents.dto.document_import_result import (
    DocumentImportStatus,
)
from app.documents.services.document_service import DocumentService


def create_import_service(
    session,
) -> DocumentImportService:
    repository = DocumentRepository(session)
    document_service = DocumentService(session)

    return DocumentImportService(
        repository=repository,
        document_service=document_service,
    )


def test_import_document(
    session,
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "example.pdf"
    content = b"Example PDF content"

    file_path.write_bytes(content)

    service = create_import_service(session)

    document = service.import_document(file_path)

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
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "example.pdf"
    file_path.write_bytes(b"Example PDF content")

    service = create_import_service(session)

    first_document = service.import_document(
        file_path
    )

    with pytest.raises(
        DocumentAlreadyImportedError
    ) as exc_info:
        service.import_document(file_path)

    assert (
        exc_info.value.existing_document_id
        == first_document.id
    )


def test_import_identical_content_from_different_path_raises_duplicate_error(
    session,
    tmp_path: Path,
) -> None:
    first_file = tmp_path / "first.pdf"
    second_file = tmp_path / "second.pdf"

    content = b"Identical document content"

    first_file.write_bytes(content)
    second_file.write_bytes(content)

    service = create_import_service(session)

    service.import_document(first_file)

    with pytest.raises(
        DocumentAlreadyImportedError
    ):
        service.import_document(second_file)


def test_import_missing_file_raises_file_not_found_error(
    session,
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "missing.pdf"

    service = create_import_service(session)

    with pytest.raises(FileNotFoundError):
        service.import_document(file_path)


def test_import_directory_raises_value_error(
    session,
    tmp_path: Path,
) -> None:
    directory = tmp_path / "documents"
    directory.mkdir()

    service = create_import_service(session)

    with pytest.raises(ValueError):
        service.import_document(directory)


def test_import_does_not_copy_or_move_file(
    session,
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "example.pdf"
    file_path.write_bytes(b"Example PDF content")

    service = create_import_service(session)

    service.import_document(file_path)

    assert file_path.exists()


def test_import_multiple_documents_continues_after_duplicate(
    session,
    tmp_path: Path,
) -> None:
    first_file = tmp_path / "first.pdf"
    duplicate_file = tmp_path / "duplicate.pdf"
    third_file = tmp_path / "third.pdf"

    first_file.write_bytes(b"same content")
    duplicate_file.write_bytes(b"same content")
    third_file.write_bytes(b"different content")

    service = create_import_service(session)

    results = service.import_documents(
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
    tmp_path: Path,
) -> None:
    valid_file = tmp_path / "valid.pdf"
    missing_file = tmp_path / "missing.pdf"
    another_valid_file = tmp_path / "another.pdf"

    valid_file.write_bytes(b"valid content")
    another_valid_file.write_bytes(b"another valid content")

    service = create_import_service(session)

    results = service.import_documents(
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