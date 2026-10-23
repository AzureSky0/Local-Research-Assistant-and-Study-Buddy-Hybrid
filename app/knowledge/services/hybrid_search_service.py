"""Search by words and by meaning, combined (Decision 035)."""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, replace

from sqlalchemy import select, tuple_
from sqlalchemy.orm import Session

from app.documents.orm import DocumentORM, DocumentPageORM
from app.knowledge.dto.search_results import (
    HIGHLIGHT_END,
    HIGHLIGHT_START,
    PassageMatch,
    SearchResults,
)
from app.knowledge.embeddings.embedder import Embedder, EmbeddingModelUnavailableError
from app.knowledge.orm.chunk_orm import ChunkORM
from app.knowledge.orm.vector_index_schema import existing_vector_tables, vector_table_name
from app.knowledge.repository.vector_repository import VectorRepository
from app.knowledge.services.evidence import is_evidence, query_terms, term_coverage
from app.knowledge.services.keyword_search_service import (
    MAX_PASSAGES,
    PASSAGES_PER_DOCUMENT,
    KeywordSearchService,
)
from app.knowledge.services.search_query import STOP_WORDS, parse_query

logger = logging.getLogger(__name__)

# How many chunks search by meaning considers before combining.
MEANING_CANDIDATES = 60

# Nearest neighbours are returned even when nothing is related; passages
# farther than this cosine distance (similarity below 0.1) are dropped.
MAX_MEANING_DISTANCE = 0.9

# Small embedding models give related and unrelated passages similar
# distances, so passages found only by meaning (no shared words) are
# limited to the closest few...
MEANING_ONLY_TOP = 20

# ...and must be mostly words: number tables embed to vague vectors.
MIN_WORD_SHARE = 0.5

# Reciprocal rank fusion constant (the usual value; Cormack et al. 2009).
RRF_K = 60

EXCERPT_WORDS = 40

# A table of contents mentions every topic but explains none ("Edmonds-Karp
# ....... 8"); pages with this many dot leaders are shown after the
# document's other matching pages.
CONTENTS_LEADERS = 3
_DOT_LEADER = re.compile(r"(?:\.\s*){5,}\d{1,4}\b")


@dataclass(slots=True)
class _Candidate:
    passage: PassageMatch
    score: float = 0.0
    by_words: bool = False
    by_meaning: bool = False


class HybridSearchService:
    """Keyword search, plus search by meaning when vectors are available.

    Results are combined with reciprocal rank fusion, which beat either
    method alone in the benchmark. Without an embedder, or before any
    passage of the workspace has been embedded, this is keyword search.
    """

    def __init__(self, session: Session, embedder: Embedder | None) -> None:
        self._session = session
        self._embedder = embedder
        self._keyword = KeywordSearchService(session)

    def search(self, workspace_id: str, text: str, limit: int = MAX_PASSAGES) -> SearchResults:
        results = self._keyword.search(workspace_id, text, limit)
        terms = query_terms(results.query)
        texts = self._page_texts(results.passages)

        # Pages that share only one or two words with a long search are
        # not evidence of anything (random text matches them too).
        if results.match_mode == "any" and results.passages:
            self._keep_evidence_pages(results, terms, texts)

        results.passages = _contents_pages_last(results.passages, texts)

        if self._embedder is None or results.too_common or not results.query:
            return results

        spec = self._embedder.spec
        if vector_table_name(spec) not in existing_vector_tables(self._session.connection()):
            return results

        vectors = VectorRepository(self._session, spec)
        results.meaning_progress = vectors.progress(workspace_id)

        if results.meaning_progress[0] == 0:
            return results

        try:
            query_vector = self._embedder.embed_query(results.query)
        except EmbeddingModelUnavailableError:
            return results

        matches = [
            match
            for match in vectors.nearest(workspace_id, query_vector, MEANING_CANDIDATES)
            if match.distance < MAX_MEANING_DISTANCE
        ]
        meaning_chunks = self._passages_for_chunks([m.chunk_id for m in matches], results.query)

        # Nearest neighbours exist for any text, so a passage found only by
        # meaning must contain enough of the search's words itself, or share
        # at least one of them and come from a document whose words support
        # the search. (Tester feedback: in one large set of lecture notes,
        # every passage of the matching document used to qualify.)
        supported = {passage.document_id for passage in results.passages}
        meaning_passages = [
            passage
            for passage, chunk_text in meaning_chunks
            if is_evidence(chunk_text, terms)
            or (passage.document_id in supported and term_coverage(chunk_text, terms) >= 1)
        ]

        results.passages = _fuse(results.passages, meaning_passages, limit)
        results.used_meaning = True
        return results

    def _page_texts(self, passages: list[PassageMatch]) -> dict[tuple[str, int], str]:
        if not passages:
            return {}
        pages = {(p.document_id, p.page_number) for p in passages}
        rows = self._session.execute(
            select(DocumentPageORM.document_id, DocumentPageORM.page_number, DocumentPageORM.text).where(
                tuple_(DocumentPageORM.document_id, DocumentPageORM.page_number).in_(pages)
            )
        ).all()
        return {(document_id, page_number): page_text for document_id, page_number, page_text in rows}

    def _keep_evidence_pages(
        self, results: SearchResults, terms: set[str], texts: dict[tuple[str, int], str]
    ) -> None:
        kept = [
            passage
            for passage in results.passages
            if is_evidence(texts.get((passage.document_id, passage.page_number), ""), terms)
        ]
        if len(kept) == len(results.passages):
            return

        # The totals counted every page with any word; the kept pages are
        # the ones worth counting.
        results.passages = kept
        results.total_passages = len(kept)
        results.total_documents = len({passage.document_id for passage in kept})
        results.widened = results.widened and bool(kept)

    def _passages_for_chunks(
        self, chunk_ids: list[str], query: str
    ) -> list[tuple[PassageMatch, str]]:
        """Turn chunks (in meaning order) into passages with an excerpt, plus the chunk text."""

        if not chunk_ids:
            return []

        rows = self._session.execute(
            select(
                ChunkORM.id,
                ChunkORM.document_id,
                ChunkORM.start_page,
                ChunkORM.end_page,
                ChunkORM.text,
                DocumentORM.file_name,
                DocumentORM.file_type,
            )
            .join(DocumentORM, DocumentORM.id == ChunkORM.document_id)
            .where(ChunkORM.id.in_(chunk_ids))
        ).all()

        by_id = {row[0]: row for row in rows}
        words = _query_words(query)
        passages = []

        for chunk_id in chunk_ids:
            row = by_id.get(chunk_id)
            if row is None:
                continue

            _, document_id, start_page, end_page, chunk_text, file_name, file_type = row

            if _word_share(chunk_text) < MIN_WORD_SHARE:
                continue

            passages.append((
                PassageMatch(
                    document_id=document_id,
                    file_name=file_name,
                    file_type=file_type,
                    page_number=start_page,
                    end_page=end_page if end_page != start_page else None,
                    snippet=_excerpt(chunk_text, words),
                    score=0.0,
                    pages_in_document=0,
                    matched_by="meaning",
                ),
                chunk_text,
            ))

        return passages


def _fuse(by_words: list[PassageMatch], by_meaning: list[PassageMatch], limit: int) -> list[PassageMatch]:
    """Reciprocal rank fusion of both lists, keyed by document and first page."""

    candidates: dict[tuple[str, int], _Candidate] = {}

    for rank, passage in enumerate(by_words):
        key = (passage.document_id, passage.page_number)
        candidate = candidates.setdefault(key, _Candidate(passage))
        candidate.by_words = True
        candidate.score += 1 / (RRF_K + rank + 1)

    for rank, passage in enumerate(by_meaning):
        # A passage found by meaning spans pages; if a page found by words
        # falls inside it, they are the same passage: keep the precise page
        # and its highlighted snippet.
        last_page = passage.end_page or passage.page_number
        overlapping = next(
            (
                existing
                for (document_id, page), existing in candidates.items()
                if document_id == passage.document_id
                and existing.by_words
                and not existing.by_meaning
                and passage.page_number <= page <= last_page
            ),
            None,
        )

        if overlapping is not None:
            candidate = overlapping
        else:
            key = (passage.document_id, passage.page_number)
            if key not in candidates and rank >= MEANING_ONLY_TOP:
                continue
            candidate = candidates.setdefault(key, _Candidate(passage))

        candidate.by_meaning = True
        candidate.score += 1 / (RRF_K + rank + 1)

    # Group by document, documents ordered by their best passage.
    groups: dict[str, list[_Candidate]] = defaultdict(list)
    for candidate in sorted(candidates.values(), key=lambda c: c.score, reverse=True):
        groups[candidate.passage.document_id].append(candidate)

    ordered = sorted(groups.values(), key=lambda group: group[0].score, reverse=True)

    fused: list[PassageMatch] = []
    for group in ordered:
        found_in_document = max(
            len(group),
            max(c.passage.pages_in_document for c in group),
        )
        for candidate in group[:PASSAGES_PER_DOCUMENT]:
            matched_by = (
                "both" if candidate.by_words and candidate.by_meaning
                else "meaning" if candidate.by_meaning
                else "words"
            )
            fused.append(
                replace(
                    candidate.passage,
                    score=candidate.score,
                    matched_by=matched_by,
                    pages_in_document=found_in_document,
                )
            )
        if len(fused) >= limit:
            break

    return fused[:limit]


def looks_like_contents(text: str) -> bool:
    """True for table-of-contents style pages (many dot leaders before page numbers)."""
    return len(_DOT_LEADER.findall(text)) >= CONTENTS_LEADERS


def _contents_pages_last(
    passages: list[PassageMatch], texts: dict[tuple[str, int], str]
) -> list[PassageMatch]:
    """Within each document, move contents pages after the other matching pages."""
    documents = list(dict.fromkeys(p.document_id for p in passages))
    order = {document_id: i for i, document_id in enumerate(documents)}
    return sorted(
        passages,
        key=lambda p: (
            order[p.document_id],
            looks_like_contents(texts.get((p.document_id, p.page_number), "")),
        ),
    )


def _word_share(text: str) -> float:
    """Share of tokens that contain letters (tables of numbers score low)."""
    tokens = text.split()
    if not tokens:
        return 0.0
    return sum(1 for token in tokens if any(c.isalpha() for c in token)) / len(tokens)


def _query_words(query: str) -> list[str]:
    parsed = parse_query(query)
    words = parsed.words + [word for phrase in parsed.phrases for word in phrase]
    return [w.lower() for w in words if len(w) >= 3 and w.lower() not in STOP_WORDS]


def _matches(token: str, words: list[str]) -> bool:
    token = token.lower()
    return any(token == w or (len(w) >= 4 and token.startswith(w[:5])) for w in words)


def _excerpt(text: str, words: list[str]) -> str:
    """About EXCERPT_WORDS words around the part of the chunk sharing most query words."""

    tokens = text.split()
    if not tokens:
        return ""

    hits = [1 if _matches(re.sub(r"\W", "", token), words) else 0 for token in tokens]
    window = min(EXCERPT_WORDS, len(tokens))

    best_start, best_hits = 0, sum(hits[:window])
    current = best_hits
    for start in range(1, len(tokens) - window + 1):
        current += hits[start + window - 1] - hits[start - 1]
        if current > best_hits:
            best_start, best_hits = start, current

    shown = [
        f"{HIGHLIGHT_START}{token}{HIGHLIGHT_END}" if hits[best_start + i] else token
        for i, token in enumerate(tokens[best_start : best_start + window])
    ]

    prefix = "…" if best_start > 0 else ""
    suffix = "…" if best_start + window < len(tokens) else ""
    return prefix + " ".join(shown) + suffix
