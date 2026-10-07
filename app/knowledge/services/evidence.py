"""How much of a search a page actually covers.

Small local models cannot tell "nothing is related" from "this is
somewhat related", and a single common word can make an unrelated page
match. A page therefore counts as evidence only when it contains a fair
share of the search's meaningful words (measured on the benchmark:
30% keeps every hard question answerable and removes nearly all matches
for random text).
"""

from __future__ import annotations

import math
import re

from app.knowledge.services.search_query import STOP_WORDS, parse_query

# Share of a search's meaningful words a page must contain.
REQUIRED_SHARE = 0.3

# Words are compared by their first letters, so simple word forms match
# ("learning" / "learned", "network" / "networks").
STEM_LENGTH = 5

_WORD = re.compile(r"\w+", re.UNICODE)


def query_terms(query: str) -> set[str]:
    """Meaningful words of a search, shortened to their stems."""

    parsed = parse_query(query)
    words = parsed.words + [word for phrase in parsed.phrases for word in phrase]
    return {
        word.lower()[:STEM_LENGTH]
        for word in words
        if len(word) >= 3 and word.lower() not in STOP_WORDS
    }


def required_terms(term_count: int) -> int:
    """How many of the terms a page must contain to count as evidence."""

    if term_count <= 2:
        return 1
    return max(2, math.ceil(term_count * REQUIRED_SHARE))


def term_coverage(text: str, terms: set[str]) -> int:
    """How many of the terms appear in the text."""

    stems = {token.lower()[:STEM_LENGTH] for token in _WORD.findall(text)}
    return sum(1 for term in terms if term in stems)


def is_evidence(text: str, terms: set[str]) -> bool:
    return bool(terms) and term_coverage(text, terms) >= required_terms(len(terms))
