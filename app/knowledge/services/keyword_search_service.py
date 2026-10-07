from __future__ import annotations

from sqlalchemy.orm import Session

from app.documents.services.document_service import DocumentService
from app.knowledge.dto.search_results import DocumentMatch, SearchResults
from app.knowledge.repository.keyword_index_repository import KeywordIndexRepository
from app.knowledge.services.search_query import (
    MatchMode,
    build_match_query,
    choose_mode,
    parse_query,
)

MAX_PASSAGES = 50
PASSAGES_PER_DOCUMENT = 3
MAX_NAME_MATCHES = 20


class KeywordSearchService:
    """Keyword search over a workspace's documents (FR-SR-001).

    Owned by the Knowledge subsystem. Documents reach the index through
    the processing pipeline; search only ever sees one workspace
    (PRD §90, knowledge isolation).
    """

    def __init__(self, session: Session) -> None:
        self._session = session
        self._index = KeywordIndexRepository(session)
        self._documents = DocumentService(session)

    def index_document(self, document_id: str) -> int:
        """Rebuild a document's index entries from its stored pages.

        Runs inside the caller's transaction (the processing stage
        commits). Returns how many pages were indexed.
        """
        return self._index.index_document(document_id)

    def search(
        self,
        workspace_id: str,
        text: str,
        limit: int = MAX_PASSAGES,
    ) -> SearchResults:
        """Find documents by name and pages by content."""

        query = text.strip()
        results = SearchResults(query=query)

        if not query:
            return results

        results.name_matches = [
            DocumentMatch(document.id, document.file_name, document.file_type)
            for document in self._documents.find_by_name(workspace_id, query, MAX_NAME_MATCHES)
        ]

        mode = choose_mode(parse_query(query))
        self._search_passages(results, workspace_id, query, mode, limit)

        # A short search that no page fully matches: show the closest pages.
        if mode is MatchMode.ALL and not results.passages:
            self._search_passages(results, workspace_id, query, MatchMode.ANY, limit)
            results.widened = bool(results.passages)

        return results

    def _search_passages(
        self,
        results: SearchResults,
        workspace_id: str,
        query: str,
        mode: MatchMode,
        limit: int,
    ) -> None:
        match_query = build_match_query(query, mode)

        if match_query is None:
            return

        results.match_mode = mode.value
        results.passages = self._index.search(
            workspace_id,
            match_query,
            limit,
            PASSAGES_PER_DOCUMENT,
        )
        results.total_passages, results.total_documents = self._index.count(
            workspace_id,
            match_query,
        )
