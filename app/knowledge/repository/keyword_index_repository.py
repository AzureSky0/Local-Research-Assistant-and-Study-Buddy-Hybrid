from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.knowledge.dto.search_results import (
    HIGHLIGHT_END,
    HIGHLIGHT_START,
    PassageMatch,
)
from app.knowledge.orm.keyword_index_schema import KEYWORD_INDEX_TABLE

SNIPPET_TOKENS = 18
ELLIPSIS = "…"


class KeywordIndexRepository:
    """Reads and writes the FTS5 keyword index.

    The repository never commits. Transaction boundaries belong
    to the service layer.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def index_document(self, document_id: str) -> int:
        """(Re)build the index entries of one document from its stored pages."""
        self.remove_document(document_id)

        result = self._session.execute(
            text(
                f"INSERT INTO {KEYWORD_INDEX_TABLE} (text, document_id, page_number) "
                "SELECT text, document_id, page_number FROM document_pages "
                "WHERE document_id = :document_id"
            ),
            {"document_id": document_id},
        )

        return int(result.rowcount or 0)  # type: ignore[attr-defined]

    def remove_document(self, document_id: str) -> None:
        self._session.execute(
            text(f"DELETE FROM {KEYWORD_INDEX_TABLE} WHERE document_id = :document_id"),
            {"document_id": document_id},
        )

    def search(self, workspace_id: str, match_query: str, limit: int) -> list[PassageMatch]:
        """Return the most relevant pages of a workspace, best first."""
        rows = self._session.execute(
            text(
                f"""
                SELECT
                    s.document_id,
                    d.file_name,
                    d.file_type,
                    s.page_number,
                    snippet({KEYWORD_INDEX_TABLE}, 0, :start, :end, :ellipsis, :tokens),
                    bm25({KEYWORD_INDEX_TABLE})
                FROM {KEYWORD_INDEX_TABLE} AS s
                JOIN documents AS d ON d.id = s.document_id
                WHERE {KEYWORD_INDEX_TABLE} MATCH :query
                  AND d.workspace_id = :workspace_id
                ORDER BY bm25({KEYWORD_INDEX_TABLE})
                LIMIT :limit
                """
            ),
            {
                "query": match_query,
                "workspace_id": workspace_id,
                "limit": limit,
                "start": HIGHLIGHT_START,
                "end": HIGHLIGHT_END,
                "ellipsis": ELLIPSIS,
                "tokens": SNIPPET_TOKENS,
            },
        )

        return [
            PassageMatch(
                document_id=row[0],
                file_name=row[1],
                file_type=row[2],
                page_number=int(row[3]),
                snippet=row[4],
                score=float(row[5]),
            )
            for row in rows
        ]

    def count(self, workspace_id: str, match_query: str) -> int:
        """Number of matching pages in a workspace."""
        return int(
            self._session.execute(
                text(
                    f"""
                    SELECT count(*)
                    FROM {KEYWORD_INDEX_TABLE} AS s
                    JOIN documents AS d ON d.id = s.document_id
                    WHERE {KEYWORD_INDEX_TABLE} MATCH :query
                      AND d.workspace_id = :workspace_id
                    """
                ),
                {"query": match_query, "workspace_id": workspace_id},
            ).scalar_one()
        )
