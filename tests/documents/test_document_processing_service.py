from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pymupdf
import pytest
from sqlalchemy.orm import Session

from app.core.tasks.task_cancellation import TaskCancellationToken
from app.documents.domain import (
    Document,
    DocumentProcessingStage,
    DocumentProcessingStatus,
)
from app.documents.processing.document_processing_service import DocumentProcessingService
from app.documents.processing.processing_stage import ProcessingCancelledError
from app.documents.repository.document_page_repository import DocumentPageRepository
from app.documents.services.document_service import DocumentService
from app.documents.tasks.process_documents_task import ProcessDocumentsTask
from app.workspace.dto.workspace_create import WorkspaceCreateDTO
from app.workspace.services.workspace_service import WorkspaceService


def make_pdf(path: Path, pages: list[str]) -> Path:
    document = pymupdf.open()
    for text in pages:
        page = document.new_page()
        if text:
            page.insert_text((72, 72), text)
    document.save(path)
    document.close()
    return path


def add_document(
    session: Session,
    workspace_id: str,
    path: Path,
    file_type: str,
    checksum: str | None = None,
) -> Document:
    return DocumentService(session).create_document(
        Document(
            id=str(uuid4()),
            workspace_id=workspace_id,
            file_name=path.name,
            original_path=str(path),
            file_size=path.stat().st_size if path.exists() else 0,
            checksum=checksum or str(uuid4()),
            file_type=file_type,
            imported_at=datetime.now(UTC),
            processing_status=DocumentProcessingStatus.PENDING,
        )
    )


def page_texts(session: Session, document_id: str) -> list[str]:
    return [page.text for page in DocumentPageRepository(session).list_for_document(document_id)]


def test_pdf_is_extracted_and_ready(session: Session, workspace_id: str, tmp_path: Path) -> None:
    path = make_pdf(tmp_path / "paper.pdf", ["Gradient descent", "Learning rate"])
    document = add_document(session, workspace_id, path, "pdf")

    result = DocumentProcessingService(session).process(document.id)

    assert result is not None
    assert result.processing_status is DocumentProcessingStatus.READY
    assert result.processed_stage is DocumentProcessingStage.KEYWORD_INDEXED
    assert result.page_count == 2
    assert result.extractor_version is not None
    texts = page_texts(session, document.id)
    assert "Gradient descent" in texts[0]
    assert "Learning rate" in texts[1]


def test_text_file_is_normalized(session: Session, workspace_id: str, tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_bytes(b"infor-\r\nmation   is\r\n\r\n\r\n\r\nkey")
    document = add_document(session, workspace_id, path, "txt")

    DocumentProcessingService(session).process(document.id)

    assert page_texts(session, document.id) == ["information is\n\nkey"]


def test_scanned_pdf_fails_with_ocr_explanation(
    session: Session, workspace_id: str, tmp_path: Path
) -> None:
    path = make_pdf(tmp_path / "scan.pdf", ["", ""])
    document = add_document(session, workspace_id, path, "pdf")

    result = DocumentProcessingService(session).process(document.id)

    assert result is not None
    assert result.processing_status is DocumentProcessingStatus.FAILED
    assert result.processing_error is not None
    assert "OCR" in result.processing_error
    assert result.page_count is None
    assert page_texts(session, document.id) == []


def test_moved_file_fails_with_reason(session: Session, workspace_id: str, tmp_path: Path) -> None:
    path = tmp_path / "notes.md"
    path.write_text("# Notes", encoding="utf-8")
    document = add_document(session, workspace_id, path, "md")
    path.unlink()

    result = DocumentProcessingService(session).process(document.id)

    assert result is not None
    assert result.processing_status is DocumentProcessingStatus.FAILED
    assert "no longer at its saved location" in (result.processing_error or "")


def test_unexpected_error_is_recorded_not_raised(
    session: Session, workspace_id: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = make_pdf(tmp_path / "paper.pdf", ["text"])
    document = add_document(session, workspace_id, path, "pdf")

    def broken_extract(self, file_path):  # type: ignore[no-untyped-def]
        raise RuntimeError("boom")
        yield  # pragma: no cover

    monkeypatch.setattr(
        "app.documents.extraction.pdf_extractor.PdfExtractor.extract", broken_extract
    )

    result = DocumentProcessingService(session).process(document.id)

    assert result is not None
    assert result.processing_status is DocumentProcessingStatus.FAILED
    assert "log file" in (result.processing_error or "")


def test_cancelled_document_returns_to_pending(
    session: Session, workspace_id: str, tmp_path: Path
) -> None:
    path = make_pdf(tmp_path / "book.pdf", ["page"] * 5)
    document = add_document(session, workspace_id, path, "pdf")

    with pytest.raises(ProcessingCancelledError):
        DocumentProcessingService(session).process(document.id, is_cancelled=lambda: True)

    reloaded = DocumentService(session).get_documents(workspace_id)[0]
    assert reloaded.processing_status is DocumentProcessingStatus.PENDING
    assert reloaded.processed_stage is DocumentProcessingStage.REGISTERED
    assert page_texts(session, document.id) == []


def test_retry_requeues_failed_document(session: Session, workspace_id: str, tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("", encoding="utf-8")
    document = add_document(session, workspace_id, path, "txt")
    service = DocumentProcessingService(session)

    failed = service.process(document.id)
    assert failed is not None and failed.processing_status is DocumentProcessingStatus.FAILED

    path.write_text("Now there is text", encoding="utf-8")
    retried = service.retry(document.id)
    assert retried is not None
    assert retried.processing_status is DocumentProcessingStatus.PENDING
    assert retried.processing_error is None

    ready = service.process(document.id)
    assert ready is not None and ready.processing_status is DocumentProcessingStatus.READY


def test_identical_file_in_another_workspace_reuses_text(
    session: Session, workspace_id: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = make_pdf(tmp_path / "textbook.pdf", ["Chapter 1", "Chapter 2"])
    other = WorkspaceService(session).create_workspace(WorkspaceCreateDTO(name="Other"))

    first = add_document(session, workspace_id, path, "pdf", checksum="same")
    second = add_document(session, other.id, path, "pdf", checksum="same")

    service = DocumentProcessingService(session)
    service.process(first.id)

    def must_not_extract(self, file_path):  # type: ignore[no-untyped-def]
        raise AssertionError("text should have been reused")
        yield  # pragma: no cover

    monkeypatch.setattr(
        "app.documents.extraction.pdf_extractor.PdfExtractor.extract", must_not_extract
    )

    result = service.process(second.id)

    assert result is not None
    assert result.processing_status is DocumentProcessingStatus.READY
    assert result.page_count == 2
    assert page_texts(session, second.id) == page_texts(session, first.id)


def test_recover_requeues_interrupted_documents(
    session: Session, workspace_id: str, tmp_path: Path
) -> None:
    path = make_pdf(tmp_path / "paper.pdf", ["text"])
    document = add_document(session, workspace_id, path, "pdf")

    # Simulate a crash while the document was being processed.
    orm = DocumentService(session)._repository.get_by_id(document.id)
    assert orm is not None
    orm.processing_status = DocumentProcessingStatus.PROCESSING
    session.commit()

    service = DocumentProcessingService(session)
    assert service.recover() == 1
    assert service.next_document_id() == document.id


def test_smaller_documents_are_processed_first(
    session: Session, workspace_id: str, tmp_path: Path
) -> None:
    big = make_pdf(tmp_path / "big.pdf", ["x" * 50] * 30)
    small = tmp_path / "small.txt"
    small.write_text("tiny", encoding="utf-8")

    big_document = add_document(session, workspace_id, big, "pdf")
    small_document = add_document(session, workspace_id, small, "txt")

    service = DocumentProcessingService(session)
    assert service.next_document_id() == small_document.id
    assert service.next_document_id(exclude={small_document.id}) == big_document.id


def test_deleted_document_is_skipped(session: Session, workspace_id: str, tmp_path: Path) -> None:
    path = make_pdf(tmp_path / "paper.pdf", ["text"])
    document = add_document(session, workspace_id, path, "pdf")
    DocumentService(session).remove_document(document.id)

    assert DocumentProcessingService(session).process(document.id) is None


def test_task_processes_every_pending_document(session: Session, workspace_id: str, tmp_path: Path) -> None:
    for index in range(3):
        path = tmp_path / f"note-{index}.md"
        path.write_text(f"# Note {index}", encoding="utf-8")
        add_document(session, workspace_id, path, "md")

    finished: list[Document] = []
    task = ProcessDocumentsTask(
        session_factory=lambda: Session(session.get_bind()),
        on_document_finished=finished.append,
    )

    processed = task.execute(TaskCancellationToken(), lambda progress: None)

    assert processed == 3
    assert all(d.processing_status is DocumentProcessingStatus.READY for d in finished)
