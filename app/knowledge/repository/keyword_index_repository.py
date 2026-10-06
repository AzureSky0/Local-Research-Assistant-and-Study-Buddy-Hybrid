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

    def search(
        self,
        workspace_id: str,
        match_query: str,
        limit: int,
        per_document: int,
    ) -> list[PassageMatch]:
        """Return the best pages of a workspace, grouped by document.

        At most `per_document` pages are returned for each document, so
        one long book cannot push every other document out of the
        results. Documents are ordered by their best page.
        """

        # FTS5 functions cannot be used inside window functions, so the
        # ranking is collected first and grouped in a second step.
        rows = self._session.execute(
            text(
                f"""
                WITH hits AS MATERIALIZED (
                    SELECT s.rowid AS id, s.document_id, s.page_number,
                           bm25({KEYWORD_INDEX_TABLE}) AS score
                    FROM {KEYWORD_INDEX_TABLE} AS s
                    JOIN documents AS d ON d.id = s.document_id
                    WHERE {KEYWORD_INDEX_TABLE} MATCH :query
                      AND d.workspace_id = :workspace_id
                ),
                ranked AS (
                    SELECT *,
                        ROW_NUMBER() OVER (PARTITION BY document_id ORDER BY score)
                            AS rank_in_document,
                        COUNT(*) OVER (PARTITION BY document_id) AS pages_in_document,
                        MIN(score) OVER (PARTITION BY document_id) AS best_in_document
                    FROM hits
                )
                SELECT r.id, r.document_id, d.file_name, d.file_type,
                       r.page_number, r.score, r.pages_in_document
                FROM ranked AS r
                JOIN documents AS d ON d.id = r.document_id
                WHERE r.rank_in_document <= :per_document
                ORDER BY r.best_in_document, r.document_id, r.score
                LIMIT :limit
                """
            ),
            {
                "query": match_query,
                "workspace_id": workspace_id,
                "per_document": per_document,
                "limit": limit,
            },
        ).all()

        snippets = self._snippets(match_query, [row[0] for row in rows])

        return [
            PassageMatch(
                document_id=row[1],
                file_name=row[2],
                file_type=row[3],
                page_number=int(row[4]),
                snippet=snippets.get(row[0], ""),
                score=float(row[5]),
                pages_in_document=int(row[6]),
            )
            for row in rows
        ]

    def _snippets(self, match_query: str, row_ids: list[int]) -> dict[int, str]:
        """Highlighted snippets, made only for the pages that are shown."""
        if not row_ids:
            return {}

        placeholders = ", ".join(f":id{index}" for index in range(len(row_ids)))
        parameters: dict[str, object] = {
            f"id{index}": row_id for index, row_id in enumerate(row_ids)
        }
        parameters.update(
            query=match_query,
            start=HIGHLIGHT_START,
            end=HIGHLIGHT_END,
            ellipsis=ELLIPSIS,
            tokens=SNIPPET_TOKENS,
        )

        rows = self._session.execute(
            text(
                f"""
                SELECT rowid,
                       snippet({KEYWORD_INDEX_TABLE}, 0, :start, :end, :ellipsis, :tokens)
                FROM {KEYWORD_INDEX_TABLE}
                WHERE {KEYWORD_INDEX_TABLE} MATCH :query
                  AND rowid IN ({placeholders})
                """
            ),
            parameters,
        )

        return {int(row[0]): row[1] for row in rows}

    def count(self, workspace_id: str, match_query: str) -> tuple[int, int]:
        """Number of matching pages and documents in a workspace."""
        row = self._session.execute(
            text(
                f"""
                SELECT count(*), count(DISTINCT s.document_id)
                FROM {KEYWORD_INDEX_TABLE} AS s
                JOIN documents AS d ON d.id = s.document_id
                WHERE {KEYWORD_INDEX_TABLE} MATCH :query
                  AND d.workspace_id = :workspace_id
                """
            ),
            {"query": match_query, "workspace_id": workspace_id},
        ).one()

        return int(row[0]), int(row[1])
