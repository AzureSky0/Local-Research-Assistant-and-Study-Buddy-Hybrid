"""Turns what a user types into a safe FTS5 query."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

# A quoted phrase, or a run of non-space characters.
_TOKEN = re.compile(r'"([^"]*)"?|(\S+)')
_WORD = re.compile(r"\w+", re.UNICODE)

# Searches with more meaningful words than this are treated as questions.
SHORT_QUERY_WORDS = 3

# Shorter partial words would match thousands of terms ("th*"), which is
# slow and not useful.
MIN_PREFIX_LENGTH = 3

# Common English words that say little about what a page is about.
# Only dropped when matching "any" word; phrases keep every word.
STOP_WORDS = frozenset(
    """
    a about above after again against all also am an and any are as at be because
    been before being below between both but by can could did do does doing down
    during each either else few for from further get gets had has have having he
    her here hers him his how i if in into is it its itself just let me more most
    my no nor not of off on once only or other our out over own same she should
    so some such than that the their them then there these they this those
    through to too under until up use used uses using very was we were what when where
    which while who whom why will with would you your
    """.split()
)


class MatchMode(StrEnum):
    ALL = "all"  # every word must appear on the page
    ANY = "any"  # any word may appear; pages with more (rarer) words rank higher


@dataclass(frozen=True, slots=True)
class ParsedQuery:
    phrases: list[list[str]]  # quoted phrases, always required
    words: list[str]  # loose words, in order
    last_word_is_open: bool  # still being typed: match as a prefix

    @property
    def meaningful_word_count(self) -> int:
        return len([w for w in self.words if w.lower() not in STOP_WORDS])

    @property
    def is_empty(self) -> bool:
        return not self.phrases and not self.words

    @property
    def only_common_words(self) -> bool:
        """True for searches like "the" or "which of": they match almost every page."""
        return not self.phrases and bool(self.words) and self.meaningful_word_count == 0


def parse_query(text: str) -> ParsedQuery:
    phrases: list[list[str]] = []
    words: list[str] = []
    last_is_open_word = False

    for match in _TOKEN.finditer(text):
        phrase, word = match.groups()

        if phrase is not None:
            phrase_words = _WORD.findall(phrase)
            if phrase_words:
                phrases.append(phrase_words)
            last_is_open_word = False
        else:
            found = _WORD.findall(word)
            words.extend(found)
            last_is_open_word = bool(found)

    open_word = (
        last_is_open_word
        and not text.endswith((" ", "\t", "\n"))
        and len(words[-1]) >= MIN_PREFIX_LENGTH
    )
    return ParsedQuery(phrases, words, open_word)


def choose_mode(query: ParsedQuery) -> MatchMode:
    """Short keyword searches need every word; questions need any word."""
    if query.meaningful_word_count > SHORT_QUERY_WORDS:
        return MatchMode.ANY
    return MatchMode.ALL


def build_match_query(text: str, mode: MatchMode = MatchMode.ALL) -> str | None:
    """Build an FTS5 MATCH expression, or None when there is nothing to search.

    - ALL: every word must appear (AND), in any order.
    - ANY: any word may appear (OR); common words such as "the" or
      "which" are left out because they match almost every page.
    - "Quoted words" must always appear together as a phrase.
    - The last word matches as a prefix while the user is still typing.
    - Punctuation and FTS5 operators are never passed through, so any
      input is safe.
    """

    query = parse_query(text)

    if query.is_empty:
        return None

    word_terms = [f'"{word}"' for word in query.words]

    if query.last_word_is_open and word_terms:
        word_terms[-1] += "*"

    phrase_terms = ['"' + " ".join(phrase) + '"' for phrase in query.phrases]

    if mode is MatchMode.ALL:
        return " ".join(phrase_terms + word_terms)

    # ANY: drop common words, unless that would leave nothing to search for.
    kept = [
        term
        for term, word in zip(word_terms, query.words)
        if word.lower() not in STOP_WORDS
    ] or word_terms

    if not kept:
        return " ".join(phrase_terms)

    any_word = "(" + " OR ".join(kept) + ")" if len(kept) > 1 else kept[0]

    # FTS5 needs an explicit AND before a bracketed group.
    return " AND ".join(phrase_terms + [any_word])
