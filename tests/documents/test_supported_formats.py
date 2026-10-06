from pathlib import Path

import pytest

from app.documents.supported_formats import get_file_type, is_supported


@pytest.mark.parametrize(
    ("file_name", "expected"),
    [
        ("paper.pdf", "pdf"),
        ("PAPER.PDF", "pdf"),
        ("notes.txt", "txt"),
        ("notes.md", "md"),
        ("notes.markdown", "md"),
        ("report.docx", None),
        ("archive.tar.gz", None),
        ("README", None),
    ],
)
def test_get_file_type(file_name: str, expected: str | None) -> None:
    assert get_file_type(Path(file_name)) == expected
    assert is_supported(Path(file_name)) is (expected is not None)
