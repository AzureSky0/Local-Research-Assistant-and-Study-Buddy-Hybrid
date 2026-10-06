from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from app.ui import document_opener
from app.ui.document_opener import build_open_command, open_document

DOCUMENT = Path("C:/Papers/Attention Is All You Need.pdf")


@pytest.mark.parametrize(
    ("viewer", "expected"),
    [
        (
            "C:/Program Files/Adobe/Acrobat DC/Acrobat/Acrobat.exe",
            ["/A", "page=12", str(DOCUMENT)],
        ),
        (
            "C:/Program Files (x86)/Adobe/Acrobat Reader DC/Reader/AcroRd32.exe",
            ["/A", "page=12", str(DOCUMENT)],
        ),
        (
            "C:/Users/me/AppData/Local/SumatraPDF/SumatraPDF.exe",
            ["-page", "12", str(DOCUMENT)],
        ),
        (
            "C:/Program Files/Google/Chrome/Application/chrome.exe",
            ["file:///C:/Papers/Attention Is All You Need.pdf#page=12"],
        ),
        (
            "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
            ["file:///C:/Papers/Attention Is All You Need.pdf#page=12"],
        ),
    ],
)
def test_page_is_passed_the_way_each_viewer_expects(
    qapp: QApplication, viewer: str, expected: list[str]
) -> None:
    command = build_open_command(Path(viewer), DOCUMENT, 12)

    assert command is not None
    assert command[0] == str(Path(viewer))
    assert command[1:] == expected


def test_unknown_viewer_has_no_page_command(qapp: QApplication) -> None:
    assert build_open_command(Path("C:/Apps/SomeViewer.exe"), DOCUMENT, 12) is None


@pytest.fixture
def launches(monkeypatch: pytest.MonkeyPatch) -> dict[str, list]:
    """Record launches instead of opening real applications."""

    calls: dict[str, list] = {"process": [], "system": []}

    def fake_start_detached(program: str, arguments: list[str]) -> bool:
        calls["process"].append([program, *arguments])
        return True

    def fake_open_with_system(path: Path) -> bool:
        calls["system"].append(path)
        return True

    monkeypatch.setattr(document_opener.QProcess, "startDetached", fake_start_detached)
    monkeypatch.setattr(document_opener, "_open_with_system", fake_open_with_system)
    return calls


def make_pdf(tmp_path: Path) -> Path:
    path = tmp_path / "paper.pdf"
    path.write_bytes(b"%PDF-1.4\n")
    return path


def test_known_viewer_opens_at_page(
    qapp: QApplication,
    tmp_path: Path,
    launches: dict[str, list],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        document_opener, "default_pdf_viewer", lambda: Path("C:/SumatraPDF/SumatraPDF.exe")
    )
    path = make_pdf(tmp_path)

    result = open_document(path, page=7)

    assert result.opened and result.at_page and result.message is None
    assert launches["process"] == [[str(Path("C:/SumatraPDF/SumatraPDF.exe")), "-page", "7", str(path)]]
    assert launches["system"] == []


def test_unknown_viewer_opens_file_and_names_the_page(
    qapp: QApplication,
    tmp_path: Path,
    launches: dict[str, list],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(document_opener, "default_pdf_viewer", lambda: Path("C:/Apps/Other.exe"))
    path = make_pdf(tmp_path)

    result = open_document(path, page=7)

    assert result.opened and not result.at_page
    assert result.message is not None and "page 7" in result.message
    assert launches["system"] == [path]


def test_without_page_the_file_opens_normally(
    qapp: QApplication, tmp_path: Path, launches: dict[str, list]
) -> None:
    path = make_pdf(tmp_path)

    result = open_document(path)

    assert result.opened and result.message is None
    assert launches["system"] == [path]
    assert launches["process"] == []


def test_moved_file_reports_a_clear_message(
    qapp: QApplication, tmp_path: Path, launches: dict[str, list]
) -> None:
    result = open_document(tmp_path / "moved.pdf", page=3)

    assert not result.opened
    assert result.message is not None and "no longer at its saved location" in result.message
    assert launches["system"] == [] and launches["process"] == []
