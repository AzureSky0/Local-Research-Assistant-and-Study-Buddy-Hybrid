"""Splits document text into overlapping chunks for retrieval (FR-KN-003).

Chunks are the units that embeddings and AI context are built from
(PRD §84). Each chunk keeps the pages it came from so answers can cite
them (PRD §85).

Text is broken into sentences (remembering where paragraphs start), and
sentences are added to a chunk until it reaches the target size, so
chunks end at sentence boundaries. The next chunk begins with the last
sentences of the previous one (overlap): an idea that spans a boundary
appears complete in at least one chunk. A Markdown heading starts a new
chunk; a small leftover of the previous section joins that section's
last chunk instead.
Text without sentence boundaries (tables, lists of numbers) is cut into
runs of words.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass

# Sizes are in words: no tokenizer is needed, and small embedding models
# read roughly 256-512 tokens, which ~220 English words fits comfortably.
TARGET_WORDS = 220
MAX_WORDS = 300
OVERLAP_WORDS = 40
# A remainder smaller than this joins the previous chunk when it fits.
MIN_FINAL_WORDS = 60

# Bump whenever chunk boundaries for the same text would change.
CHUNKER_VERSION = f"sentences-{TARGET_WORDS}-{MAX_WORDS}-{OVERLAP_WORDS}-1"

_PARAGRAPH_BREAK = re.compile(r"\n\s*\n")
_SENTENCE_END = re.compile(r"(?<=[.!?…])\s+(?=[\"'“‘(\[]?[A-Z0-9À-ÖØ-Þ])")
_MARKDOWN_HEADING = re.compile(r"^#{1,6}\s")


@dataclass(frozen=True, slots=True)
class Chunk:
    """A passage of a document, with the pages it spans."""

    index: int
    text: str
    start_page: int
    end_page: int
    word_count: int


@dataclass(frozen=True, slots=True)
class _Unit:
    """A sentence (or a run of words) that chunks are built from."""

    text: str
    page: int
    words: int
    starts_paragraph: bool
    starts_section: bool


def chunk_pages(pages: Iterable[tuple[int, str]]) -> list[Chunk]:
    """Split pages, given as (page number, text), into chunks."""

    chunks: list[Chunk] = []
    last_units: list[_Unit] = []  # sentences of the most recent chunk
    carried: list[_Unit] = []  # overlap taken from the previous chunk
    fresh: list[_Unit] = []  # sentences added since the previous chunk

    def emit() -> None:
        nonlocal carried, fresh, last_units

        units = carried + fresh
        chunks.append(_make_chunk(len(chunks), units))
        last_units = units
        carried = _overlap_tail(units)
        fresh = []

    def finish_section() -> None:
        """Emit what is left; a small remainder extends the previous chunk."""
        nonlocal carried, fresh, last_units

        if fresh:
            fits = _words(last_units) + _words(fresh) <= MAX_WORDS

            if chunks and _words(fresh) < MIN_FINAL_WORDS and fits:
                last_units = last_units + fresh
                chunks[-1] = _make_chunk(chunks[-1].index, last_units)
            else:
                emit()

        # A new section never starts with the previous section's tail.
        carried, fresh = [], []

    for unit in _units(pages):
        if unit.starts_section and (fresh or carried):
            finish_section()
        elif fresh and _words(carried) + _words(fresh) + unit.words > MAX_WORDS:
            emit()

        fresh.append(unit)

        if _words(carried) + _words(fresh) >= TARGET_WORDS:
            emit()

    finish_section()
    return chunks


def _words(units: list[_Unit]) -> int:
    return sum(unit.words for unit in units)


def _make_chunk(index: int, units: list[_Unit]) -> Chunk:
    return Chunk(
        index=index,
        text=_join(units),
        start_page=units[0].page,
        end_page=units[-1].page,
        word_count=sum(unit.words for unit in units),
    )


def _units(pages: Iterable[tuple[int, str]]) -> Iterator[_Unit]:
    for page_number, text in pages:
        for paragraph in _PARAGRAPH_BREAK.split(text):
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            starts_section = bool(_MARKDOWN_HEADING.match(paragraph))

            for position, piece in enumerate(_pieces(paragraph)):
                yield _Unit(
                    text=piece,
                    page=page_number,
                    words=len(piece.split()),
                    starts_paragraph=position == 0,
                    starts_section=starts_section and position == 0,
                )


def _pieces(paragraph: str) -> Iterator[str]:
    """Sentences of a paragraph; over-long sentences become word runs."""

    for sentence in _SENTENCE_END.split(paragraph):
        words = sentence.split()

        if not words:
            continue

        if len(words) <= MAX_WORDS:
            yield " ".join(words)
            continue

        for start in range(0, len(words), TARGET_WORDS):
            yield " ".join(words[start : start + TARGET_WORDS])


def _join(units: list[_Unit]) -> str:
    """Rebuild text, keeping paragraph breaks between paragraphs."""

    parts: list[str] = []

    for position, unit in enumerate(units):
        if position > 0:
            parts.append("\n\n" if unit.starts_paragraph else " ")
        parts.append(unit.text)

    return "".join(parts)


def _overlap_tail(units: list[_Unit]) -> list[_Unit]:
    """The last sentences of a chunk, up to OVERLAP_WORDS, to start the next one."""

    tail: list[_Unit] = []
    words = 0

    for unit in reversed(units[1:]):  # never carry over the whole chunk
        if words + unit.words > OVERLAP_WORDS:
            break
        tail.insert(0, unit)
        words += unit.words

    return tail
