"""Document formats supported by the core application (Decision 022).

This is a simple lookup for v0.2. In v0.3 it is replaced by the
capability registry, where each document reader declares the
formats it handles (Decision 028).
"""

from __future__ import annotations

from pathlib import Path

PDF = "pdf"
TEXT = "txt"
MARKDOWN = "md"

TEXT_FILE_TYPES = frozenset({TEXT, MARKDOWN})

SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".pdf": PDF,
    ".txt": TEXT,
    ".md": MARKDOWN,
    ".markdown": MARKDOWN,
}

SUPPORTED_FORMATS_DESCRIPTION = "PDF, plain text (.txt), and Markdown (.md)"


def get_file_type(file_path: Path) -> str | None:
    """Return the document file type for a path, or None if unsupported."""
    return SUPPORTED_EXTENSIONS.get(file_path.suffix.lower())


def is_supported(file_path: Path) -> bool:
    """Return whether the file extension is a supported document format."""
    return get_file_type(file_path) is not None
