"""Benchmark the document pipeline on a corpus folder (Decision 034).

Usage (project environment):
    python scripts/benchmark/benchmark_pipeline.py CORPUS_DIR RESULTS_DIR

Runs the application's real import and processing code against a
throwaway data directory, then measures keyword search speed and
quality on scripts/benchmark/questions.json. Writes results.json and
keeps the database for the embedding benchmark.
"""

from __future__ import annotations

import json
import os
import re
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

CORPUS = Path(sys.argv[1]).resolve()
RESULTS = Path(sys.argv[2]).resolve()
RESULTS.mkdir(parents=True, exist_ok=True)

# A fresh data directory, so the benchmark never touches real user data.
os.environ["LOCI_DATA_DIR"] = str(RESULTS / "data")

from sqlalchemy import text  # noqa: E402

from app.core.paths import ensure_app_directories  # noqa: E402
from app.database.init_db import initialize_database  # noqa: E402
from app.database.session import create_session  # noqa: E402
from app.documents.processing.document_processing_service import (  # noqa: E402
    DocumentProcessingService,
    default_stages,
)
from app.documents.processing.processing_stage import ProcessingContext, ProcessingStage  # noqa: E402
from app.documents.services.document_import_service import DocumentImportService  # noqa: E402
from app.documents.services.document_service import DocumentService  # noqa: E402
from app.knowledge.services.keyword_search_service import KeywordSearchService  # noqa: E402
from app.workspace.dto.workspace_create import WorkspaceCreateDTO  # noqa: E402
from app.workspace.services.workspace_service import WorkspaceService  # noqa: E402

QUESTIONS = json.loads((Path(__file__).parent / "questions.json").read_text(encoding="utf-8"))
_WORD = re.compile(r"\w+")


class TimedStage(ProcessingStage):
    """Wraps a stage to record how long it takes."""

    def __init__(self, inner: ProcessingStage, timings: dict[str, list[float]]) -> None:
        self._inner = inner
        self._timings = timings

    @property
    def completes(self):  # type: ignore[no-untyped-def]
        return self._inner.completes

    def run(self, context: ProcessingContext) -> None:
        start = time.perf_counter()
        self._inner.run(context)
        self._timings[self._inner.completes.value].append(time.perf_counter() - start)


def arxiv_id(file_name: str) -> str:
    return file_name.removesuffix(".pdf").replace("_", "/")


def keyword_ranking(session, workspace_id: str, question: str, mode: str) -> list[str]:  # type: ignore[no-untyped-def]
    """Document ids ranked by their best matching page."""
    if mode == "app":
        # What the Library search box does.
        results = KeywordSearchService(session).search(workspace_id, question, limit=50)
        ranked = []
        for passage in results.passages:
            if passage.document_id not in ranked:
                ranked.append(passage.document_id)
        return ranked

    if mode == "all_words":
        # The original rule: every word must appear.
        from app.knowledge.services.search_query import MatchMode, build_match_query

        match = build_match_query(question, MatchMode.ALL)
        rows = session.execute(
            text(
                "WITH hits AS MATERIALIZED (SELECT document_id, bm25(page_search) AS score "
                "FROM page_search WHERE page_search MATCH :q) "
                "SELECT document_id, min(score) AS best FROM hits "
                "GROUP BY document_id ORDER BY best LIMIT 20"
            ),
            {"q": match},
        ).all()
        return [row[0] for row in rows]

    # "or": any word may match; BM25 ranks pages with more (rarer) words higher.
    words = [w for w in _WORD.findall(question.lower()) if len(w) > 2]
    if not words:
        return []
    match = " OR ".join(f'"{w}"' for w in words)
    rows = session.execute(
        text(
            # FTS5 functions cannot be used inside aggregates: rank first.
            "WITH hits AS MATERIALIZED (SELECT document_id, bm25(page_search) AS score "
            "FROM page_search WHERE page_search MATCH :q) "
            "SELECT document_id, min(score) AS best FROM hits "
            "GROUP BY document_id ORDER BY best LIMIT 20"
        ),
        {"q": match},
    ).all()
    return [row[0] for row in rows]


def score(rankings: list[list[str]], answers: list[str]) -> dict[str, float]:
    hits1 = hits5 = 0
    reciprocal = 0.0
    for ranking, answer in zip(rankings, answers):
        if answer in ranking[:1]:
            hits1 += 1
        if answer in ranking[:5]:
            hits5 += 1
        if answer in ranking:
            reciprocal += 1 / (ranking.index(answer) + 1)
    n = len(answers)
    result = {"recall@1": hits1 / n, "recall@5": hits5 / n, "mrr": reciprocal / n}

    for style in ("standard", "student", "hard"):
        indexes = [i for i, q in enumerate(QUESTIONS) if q.get("style", "standard") == style]
        if indexes:
            hits = sum(1 for i in indexes if answers[i] in rankings[i][:5])
            result[f"{style}_recall@5"] = hits / len(indexes)
    return result


def main() -> None:
    ensure_app_directories()
    initialize_database()

    results: dict = {"corpus": str(CORPUS)}

    with create_session() as session:
        workspace = WorkspaceService(session).create_workspace(WorkspaceCreateDTO(name="Benchmark"))
        workspace_id = workspace.id

        # Import -----------------------------------------------------------------
        start = time.perf_counter()
        imported = DocumentImportService(DocumentService(session)).import_folder(workspace_id, CORPUS)
        import_seconds = time.perf_counter() - start

        statuses = defaultdict(int)
        for result in imported:
            statuses[result.status.value] += 1
        results["import"] = {"seconds": round(import_seconds, 2), "statuses": dict(statuses)}
        print(f"Imported in {import_seconds:.1f}s: {dict(statuses)}", flush=True)

        # Processing ------------------------------------------------------------
        timings: dict[str, list[float]] = defaultdict(list)
        stages = [TimedStage(stage, timings) for stage in default_stages()]
        service = DocumentProcessingService(session, stages)

        per_document: list[float] = []
        failures: dict[str, str] = {}
        start = time.perf_counter()

        while (document_id := service.next_document_id(exclude=failures.keys())) is not None:
            t0 = time.perf_counter()
            document = service.process(document_id)
            per_document.append(time.perf_counter() - t0)
            if document is not None and document.processing_error:
                failures[document.file_name] = document.processing_error
                failures[document_id] = document.processing_error

        processing_seconds = time.perf_counter() - start

        counts = session.execute(
            text(
                "SELECT (SELECT count(*) FROM documents WHERE processing_status='READY'), "
                "(SELECT count(*) FROM document_pages), (SELECT count(*) FROM chunks), "
                "(SELECT sum(word_count) FROM chunks)"
            )
        ).one()

        results["processing"] = {
            "seconds": round(processing_seconds, 2),
            "documents_ready": counts[0],
            "pages": counts[1],
            "chunks": counts[2],
            "chunk_words": counts[3],
            "failed": {k: v for k, v in failures.items() if k.endswith(".pdf")},
            "per_document_seconds": {
                "median": round(statistics.median(per_document), 3),
                "p95": round(sorted(per_document)[int(len(per_document) * 0.95) - 1], 3),
                "max": round(max(per_document), 3),
            },
            "stage_seconds_total": {k: round(sum(v), 2) for k, v in timings.items()},
        }
        print(f"Processed in {processing_seconds:.1f}s: {results['processing']}", flush=True)

        # Keyword search ----------------------------------------------------------
        id_by_document = {
            row[0]: arxiv_id(row[1])
            for row in session.execute(text("SELECT id, file_name FROM documents")).all()
        }
        answers = [q["answer"] for q in QUESTIONS]

        for mode in ("all_words", "or", "app"):
            latencies = []
            rankings = []
            for question in QUESTIONS:
                t0 = time.perf_counter()
                ranked = keyword_ranking(session, workspace_id, question["question"], mode)
                latencies.append((time.perf_counter() - t0) * 1000)
                rankings.append([id_by_document[d] for d in ranked])

            results[f"keyword_{mode}"] = {
                **{k: round(v, 3) for k, v in score(rankings, answers).items()},
                "no_results": sum(1 for r in rankings if not r),
                "latency_ms": {
                    "median": round(statistics.median(latencies), 1),
                    "max": round(max(latencies), 1),
                },
            }
            print(f"Keyword ({mode}): {results[f'keyword_{mode}']}", flush=True)

        # Typical search-box queries (short), for latency at full size.
        short_latencies = []
        for query in ["gradient", "attention", "transformer", "neural network", "learning rate", "the"]:
            t0 = time.perf_counter()
            KeywordSearchService(session).search(workspace_id, query)
            short_latencies.append((time.perf_counter() - t0) * 1000)
        results["search_box_latency_ms"] = {
            "median": round(statistics.median(short_latencies), 1),
            "max": round(max(short_latencies), 1),
        }

    db_path = RESULTS / "data" / "database" / "local_research.db"
    results["database_mb"] = round(db_path.stat().st_size / 1024 / 1024, 1)
    results["database_path"] = str(db_path)

    (RESULTS / "pipeline_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
