"""Turns what a user types into a safe FTS5 query."""

from __future__ import annotations

import re

# A quoted phrase, or a run of non-space characters.
_TOKEN = re.compile(r'"([^"]*)"?|(\S+)')
_WORD = re.compile(r"\w+", re.UNICODE)


def build_match_query(text: str) -> str | None:
    """Build an FTS5 MATCH expression, or None when there is nothing to search.

    - Words must all appear (AND), in any order.
    - "Quoted words" must appear together as a phrase.
    - The last word matches as a prefix while the user is still typing.
    - Punctuation and FTS5 operators are never passed through, so any
      input is safe.
    """

    parts: list[str] = []
    last_is_open_word = False

    for match in _TOKEN.finditer(text):
        phrase, word = match.groups()

        if phrase is not None:
            words = _WORD.findall(phrase)
            if words:
                parts.append('"' + " ".join(words) + '"')
            last_is_open_word = False
        else:
            words = _WORD.findall(word)
            parts.extend(f'"{w}"' for w in words)
            last_is_open_word = bool(words)

    if not parts:
        return None

    if last_is_open_word and not text.endswith((" ", "\t", "\n")):
        parts[-1] += "*"

    return " ".join(parts)
