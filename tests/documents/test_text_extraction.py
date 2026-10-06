from pathlib import Path

import pymupdf
import pytest

from app.core.capabilities import CapabilityRegistry
from app.documents.exceptions import ExtractionError
from app.documents.extraction.extractor_registry import (
    ExtractorRegistry,
    default_extractor_registry,
)
from app.documents.extraction.pdf_extractor import PdfExtractor
from app.documents.extraction.text_extractor import TextExtractor, decode_text
from app.documents.extraction.text_normalizer import normalize_text


def make_pdf(path: Path, pages: list[str]) -> Path:
    document = pymupdf.open()

    for text in pages:
        page = document.new_page()
        if text:
            page.insert_text((72, 72), text)

    document.save(path)
    document.close()
    return path


# PDF -------------------------------------------------------------------------


def test_pdf_pages_are_extracted_in_order(tmp_path: Path) -> None:
    path = make_pdf(tmp_path / "paper.pdf", ["First page", "Second page", "Third page"])

    pages = list(PdfExtractor().extract(path))

    assert [page.page_number for page in pages] == [1, 2, 3]
    assert "First page" in pages[0].text
    assert "Third page" in pages[2].text


def test_password_protected_pdf_gives_clear_reason(tmp_path: Path) -> None:
    document = pymupdf.open()
    document.new_page().insert_text((72, 72), "secret")
    path = tmp_path / "locked.pdf"
    document.save(
        path,
        encryption=pymupdf.PDF_ENCRYPT_AES_256,
        owner_pw="owner",
        user_pw="user",
    )
    document.close()

    with pytest.raises(ExtractionError, match="password-protected"):
        list(PdfExtractor().extract(path))


def test_damaged_pdf_gives_clear_reason(tmp_path: Path) -> None:
    path = tmp_path / "damaged.pdf"
    path.write_bytes(b"%PDF-1.4\nthis is not really a pdf")

    with pytest.raises(ExtractionError, match="damaged"):
        list(PdfExtractor().extract(path))


def test_missing_pdf_gives_clear_reason(tmp_path: Path) -> None:
    with pytest.raises(ExtractionError):
        list(PdfExtractor().extract(tmp_path / "moved.pdf"))


# Text ------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("encoding", "text"),
    [
        ("utf-8", "Grüße — naïve café"),
        ("utf-8-sig", "Grüße — naïve café"),
        ("utf-16", "Grüße — naïve café"),
        ("cp1252", "Grüße – naïve café"),
    ],
)
def test_text_encodings_are_detected(encoding: str, text: str) -> None:
    assert decode_text(text.encode(encoding)) == text


def test_text_file_is_one_page(tmp_path: Path) -> None:
    path = tmp_path / "notes.md"
    path.write_bytes(b"# Title\n\nSome notes")

    pages = list(TextExtractor().extract(path))

    assert len(pages) == 1
    assert pages[0].page_number == 1
    assert pages[0].text == "# Title\n\nSome notes"


def test_missing_text_file_gives_clear_reason(tmp_path: Path) -> None:
    with pytest.raises(ExtractionError, match="no longer at its saved location"):
        list(TextExtractor().extract(tmp_path / "moved.txt"))


# Normalization -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("infor-\nmation", "information"),
        ("too    many   spaces", "too many spaces"),
        ("line one\r\nline two", "line one\nline two"),
        ("a\n\n\n\n\nb", "a\n\nb"),
        ("soft­hyphen and zero​width", "softhyphen and zerowidth"),
        ("café", "café"),
        ("  padded  \n", "padded"),
    ],
)
def test_normalize_text(raw: str, expected: str) -> None:
    assert normalize_text(raw) == expected


# Registry ------------------------------------------------------------------------


def test_default_registry_reads_core_formats() -> None:
    registry = default_extractor_registry()

    assert isinstance(registry.extractor_for("pdf"), PdfExtractor)
    assert isinstance(registry.extractor_for("txt"), TextExtractor)
    assert isinstance(registry.extractor_for("md"), TextExtractor)


def test_unknown_format_reports_missing_capability() -> None:
    with pytest.raises(ExtractionError, match="docx"):
        default_extractor_registry().extractor_for("docx")


def test_extension_can_replace_a_built_in_reader() -> None:
    capabilities: CapabilityRegistry = CapabilityRegistry()
    registry = ExtractorRegistry(capabilities)
    registry.register(TextExtractor())

    class BetterMarkdownExtractor(TextExtractor):
        @property
        def file_types(self) -> frozenset[str]:
            return frozenset({"md"})

    better = BetterMarkdownExtractor()
    registry.register(better)

    assert registry.extractor_for("md") is better
    assert capabilities.has("document.md.read")
    assert capabilities.has("document.txt.read")
