"""Cleans extracted text so search and chunking see consistent input."""

from __future__ import annotations

import re
import unicodedata

# Part of the cache key for extracted text: bump when output changes.
NORMALIZER_VERSION = "1"

# Characters that survive PDF extraction but carry no meaning in text.
_INVISIBLE = dict.fromkeys(
    map(ord, "­​‌‍⁠﻿\x00"),
    None,
)

# "infor-\nmation" -> "information" (a word broken across lines).
_HYPHENATED_LINE_BREAK = re.compile(r"(\w)-\n(\w)")
_SPACES = re.compile(r"[ \t\f\v ]+")
_SPACE_AROUND_NEWLINE = re.compile(r" ?\n ?")
_BLANK_LINES = re.compile(r"\n{3,}")


def normalize_text(text: str) -> str:
    """Normalize extracted text.

    - Unicode NFC, so the same word always has the same characters.
    - Windows and old Mac line endings become "\\n".
    - Invisible characters (soft hyphens, zero-width spaces, NUL) are removed.
    - Words hyphenated across a line break are joined.
    - Runs of spaces collapse to one; at most one blank line in a row.
    """

    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.translate(_INVISIBLE)
    text = _SPACES.sub(" ", text)
    text = _SPACE_AROUND_NEWLINE.sub("\n", text)
    text = _HYPHENATED_LINE_BREAK.sub(r"\1\2", text)
    text = _BLANK_LINES.sub("\n\n", text)

    return text.strip()
