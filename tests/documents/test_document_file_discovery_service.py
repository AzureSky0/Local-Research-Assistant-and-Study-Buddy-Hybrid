import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from app.documents.services.document_file_discovery_service import (
    DocumentFileDiscoveryService,
)


@pytest.fixture
def discovery() -> DocumentFileDiscoveryService:
    return DocumentFileDiscoveryService()


def create_files(root: Path, relative_paths: list[str]) -> None:
    for relative_path in relative_paths:
        file_path = root / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("content", encoding="utf-8")


def names(paths: list[Path], root: Path) -> list[str]:
    return [path.relative_to(root).as_posix() for path in paths]


def test_discovers_supported_files_recursively(
    discovery: DocumentFileDiscoveryService,
    tmp_path: Path,
) -> None:
    create_files(
        tmp_path,
        [
            "b.pdf",
            "a.md",
            "chapters/one.txt",
            "chapters/deep/two.markdown",
        ],
    )

    result = discovery.discover(tmp_path)

    assert names(result.supported_files, tmp_path) == [
        "a.md",
        "b.pdf",
        "chapters/one.txt",
        "chapters/deep/two.markdown",
    ]
    assert result.unsupported_files == []
    assert result.inaccessible_paths == []


def test_reports_unsupported_files(
    discovery: DocumentFileDiscoveryService,
    tmp_path: Path,
) -> None:
    create_files(tmp_path, ["paper.pdf", "slides.pptx", "data.xlsx"])

    result = discovery.discover(tmp_path)

    assert names(result.supported_files, tmp_path) == ["paper.pdf"]
    assert names(result.unsupported_files, tmp_path) == ["data.xlsx", "slides.pptx"]


def test_non_recursive_scan_ignores_subfolders(
    discovery: DocumentFileDiscoveryService,
    tmp_path: Path,
) -> None:
    create_files(tmp_path, ["top.pdf", "sub/nested.pdf"])

    result = discovery.discover(tmp_path, recursive=False)

    assert names(result.supported_files, tmp_path) == ["top.pdf"]


def test_skips_dot_files_dot_folders_and_office_lock_files(
    discovery: DocumentFileDiscoveryService,
    tmp_path: Path,
) -> None:
    create_files(
        tmp_path,
        [
            "visible.pdf",
            ".hidden.pdf",
            ".git/notes.md",
            "~$report.docx",
        ],
    )

    result = discovery.discover(tmp_path)

    assert names(result.supported_files, tmp_path) == ["visible.pdf"]
    assert result.unsupported_files == []


@pytest.mark.skipif(sys.platform != "win32", reason="Windows file attributes")
def test_skips_windows_hidden_and_system_files(
    discovery: DocumentFileDiscoveryService,
    tmp_path: Path,
) -> None:
    create_files(tmp_path, ["visible.pdf", "secret.pdf", "desktop.ini"])

    subprocess.run(["attrib", "+h", str(tmp_path / "secret.pdf")], check=True)
    subprocess.run(["attrib", "+s", "+h", str(tmp_path / "desktop.ini")], check=True)

    attributes = os.stat(tmp_path / "secret.pdf").st_file_attributes
    assert attributes & stat.FILE_ATTRIBUTE_HIDDEN

    result = discovery.discover(tmp_path)

    assert names(result.supported_files, tmp_path) == ["visible.pdf"]
    assert result.unsupported_files == []


def test_missing_folder_raises_file_not_found(
    discovery: DocumentFileDiscoveryService,
    tmp_path: Path,
) -> None:
    with pytest.raises(FileNotFoundError):
        discovery.discover(tmp_path / "missing")


def test_file_path_raises_not_a_directory(
    discovery: DocumentFileDiscoveryService,
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "file.pdf"
    file_path.write_text("content", encoding="utf-8")

    with pytest.raises(NotADirectoryError):
        discovery.discover(file_path)


def test_unreadable_subfolder_is_reported(
    discovery: DocumentFileDiscoveryService,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_files(tmp_path, ["ok.pdf", "locked/secret.pdf"])

    locked = tmp_path / "locked"
    real_scandir = os.scandir

    def fake_scandir(path):  # type: ignore[no-untyped-def]
        if Path(path) == locked:
            raise PermissionError(13, "Permission denied", str(locked))
        return real_scandir(path)

    monkeypatch.setattr(os, "scandir", fake_scandir)

    result = discovery.discover(tmp_path)

    assert names(result.supported_files, tmp_path) == ["ok.pdf"]
    assert result.inaccessible_paths == [locked]
