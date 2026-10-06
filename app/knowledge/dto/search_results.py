from __future__ import annotations

from dataclasses import dataclass, field

# Markers around matched words in snippets. Control characters cannot
# appear in normalized document text, so they are unambiguous.
HIGHLIGHT_START = "\x02"
HIGHLIGHT_END = "\x03"


@dataclass(frozen=True, slots=True)
class DocumentMatch:
    """A document whose file name matches the search."""

    document_id: str
    file_name: str
    file_type: str


@dataclass(frozen=True, slots=True)
class PassageMatch:
    """A page whose text matches the search."""

    document_id: str
    file_name: str
    file_type: str
    page_number: int
    snippet: str  # matched words wrapped in HIGHLIGHT_START / HIGHLIGHT_END
    score: float  # lower is more relevant (FTS5 bm25)
    pages_in_document: int  # how many pages of this document match in total


@dataclass(slots=True)
class SearchResults:
    query: str
    name_matches: list[DocumentMatch] = field(default_factory=list)
    passages: list[PassageMatch] = field(default_factory=list)
    total_passages: int = 0
    total_documents: int = 0

    @property
    def is_empty(self) -> bool:
        return not self.name_matches and not self.passages

