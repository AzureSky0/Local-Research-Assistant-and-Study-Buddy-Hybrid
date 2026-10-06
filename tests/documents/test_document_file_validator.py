from pathlib import Path

import pytest

from app.documents.exceptions import (
    InvalidDocumentError,
    UnsupportedDocumentTypeError,
)
from app.documents.services.document_file_validator import DocumentFileValidator


@pytest.fixture
def validator() -> DocumentFileValidator:
    return DocumentFileValidator()


def test_valid_pdf_returns_pdf_type(validator: DocumentFileValidator, tmp_path: Path) -> None:
    file_path = tmp_path / "paper.pdf"
    file_path.write_bytes(b"%PDF-1.7\n...")

    assert validator.validate(file_path) == "pdf"


def test_pdf_header_after_leading_bytes_is_accepted(
    validator: DocumentFileValidator,
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "paper.pdf"
    file_path.write_bytes(b"\r\n" * 10 + b"%PDF-1.4\n...")

    assert validator.validate(file_path) == "pdf"


def test_text_and_markdown_files_are_accepted(
    validator: DocumentFileValidator,
    tmp_path: Path,
) -> None:
    text_file = tmp_path / "notes.txt"
    markdown_file = tmp_path / "README.MD"

    text_file.write_text("Some notes", encoding="utf-8")
    markdown_file.write_text("# Title", encoding="utf-8")

    assert validator.validate(text_file) == "txt"
    assert validator.validate(markdown_file) == "md"


def test_utf16_text_file_is_accepted(
    validator: DocumentFileValidator,
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "notepad.txt"
    file_path.write_text("Saved by Notepad", encoding="utf-16")

    assert validator.validate(file_path) == "txt"


def test_missing_file_raises_file_not_found(
    validator: DocumentFileValidator,
    tmp_path: Path,
) -> None:
    with pytest.raises(FileNotFoundError):
        validator.validate(tmp_path / "missing.pdf")


def test_directory_raises_value_error(
    validator: DocumentFileValidator,
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError):
        validator.validate(tmp_path)


@pytest.mark.parametrize("file_name", ["report.docx", "data.xlsx", "photo.png", "README"])
def test_unsupported_formats_raise_error(
    validator: DocumentFileValidator,
    tmp_path: Path,
    file_name: str,
) -> None:
    file_path = tmp_path / file_name
    file_path.write_bytes(b"content")

    with pytest.raises(UnsupportedDocumentTypeError):
        validator.validate(file_path)


def test_unsupported_error_explains_file_without_extension(
    validator: DocumentFileValidator,
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "LICENSE"
    file_path.write_text("MIT", encoding="utf-8")

    with pytest.raises(UnsupportedDocumentTypeError) as exc_info:
        validator.validate(file_path)

    assert "without an extension" in str(exc_info.value)


def test_empty_file_is_rejected(
    validator: DocumentFileValidator,
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "empty.txt"
    file_path.touch()

    with pytest.raises(InvalidDocumentError, match="empty"):
        validator.validate(file_path)


def test_file_with_pdf_extension_but_no_pdf_header_is_rejected(
    validator: DocumentFileValidator,
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "renamed.pdf"
    file_path.write_text("This is just text", encoding="utf-8")

    with pytest.raises(InvalidDocumentError, match="not a valid PDF"):
        validator.validate(file_path)


def test_binary_file_with_text_extension_is_rejected(
    validator: DocumentFileValidator,
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "program.txt"
    file_path.write_bytes(b"MZ\x90\x00\x03\x00\x00\x00")

    with pytest.raises(InvalidDocumentError, match="text"):
        validator.validate(file_path)
