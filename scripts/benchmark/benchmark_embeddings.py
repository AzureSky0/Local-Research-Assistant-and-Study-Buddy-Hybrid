"""Benchmark embedding models and vector stores on benchmark chunks (Decision 034).

Runs in a separate benchmark environment (not the app's):

    python scripts/benchmark/benchmark_embeddings.py DB_PATH RESULTS_DIR \
        --backend fastembed|sentence-transformers --model MODEL [--stores]

Reads chunks from the database written by benchmark_pipeline.py and
measures load time, embedding speed, peak memory, retrieval quality
(semantic and hybrid with keyword search) and, with --stores, the
sqlite-vec and ChromaDB vector stores.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
import statistics
import sys
import tempfile
import threading
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import psutil

HERE = Path(__file__).parent
QUESTIONS = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))
MODEL_CACHE = HERE.parent.parent / "data" / "benchmark" / "models"
DEFAULT_BATCH_SIZE = 16
TOP_CHUNKS = 50
RRF_K = 60
_WORD = re.compile(r"\w+")

# BGE and Arctic models expect this instruction in front of queries (not passages).
RETRIEVAL_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
PREFIXED_MODELS = ("bge", "arctic-embed")


class PeakMemory:
    """Samples this process's memory use in the background."""

    def __init__(self) -> None:
        self._process = psutil.Process()
        self.peak = self._process.memory_info().rss
        self._running = True
        self._thread = threading.Thread(target=self._sample, daemon=True)
        self._thread.start()

    def _sample(self) -> None:
        while self._running:
            self.peak = max(self.peak, self._process.memory_info().rss)
            time.sleep(0.05)

    def stop(self) -> float:
        self._running = False
        self._thread.join()
        return round(self.peak / 1024 / 1024)


def folder_mb(path: Path) -> float:
    return round(sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / 1024 / 1024, 1)


def arxiv_id(file_name: str) -> str:
    return file_name.removesuffix(".pdf").replace("_", "/")


def load_chunks(db_path: Path) -> tuple[list[str], list[str]]:
    connection = sqlite3.connect(db_path)
    rows = connection.execute(
        "SELECT c.text, d.file_name FROM chunks c JOIN documents d ON d.id = c.document_id "
        "ORDER BY d.file_name, c.chunk_index"
    ).fetchall()
    connection.close()
    return [row[0] for row in rows], [arxiv_id(row[1]) for row in rows]


def keyword_rankings(db_path: Path) -> list[list[str]]:
    """Document rankings from FTS5 with OR semantics (see benchmark_pipeline)."""
    connection = sqlite3.connect(db_path)
    rankings = []
    for question in QUESTIONS:
        words = [w for w in _WORD.findall(question["question"].lower()) if len(w) > 2]
        rows = connection.execute(
            "WITH hits AS MATERIALIZED (SELECT document_id, bm25(page_search) AS score "
            "FROM page_search WHERE page_search MATCH ?) "
            "SELECT d.file_name, min(h.score) AS best FROM hits h "
            "JOIN documents d ON d.id = h.document_id "
            "GROUP BY h.document_id ORDER BY best LIMIT 50",
            (" OR ".join(f'"{w}"' for w in words),),
        ).fetchall()
        rankings.append([arxiv_id(row[0]) for row in rows])
    connection.close()
    return rankings


def document_ranking(chunk_order: list[int], chunk_docs: list[str]) -> list[str]:
    ranked: list[str] = []
    for index in chunk_order:
        if chunk_docs[index] not in ranked:
            ranked.append(chunk_docs[index])
    return ranked


def reciprocal_rank_fusion(*rankings: list[str]) -> list[str]:
    scores: dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for position, item in enumerate(ranking):
            scores[item] += 1 / (RRF_K + position + 1)
    return sorted(scores, key=scores.get, reverse=True)  # type: ignore[arg-type]


def score(rankings: list[list[str]]) -> dict[str, float]:
    """Recall@1, recall@5 and MRR overall, plus recall@5 per question style."""
    answers = [q["answer"] for q in QUESTIONS]

    def recall(indexes: list[int], k: int) -> float:
        return round(sum(1 for i in indexes if answers[i] in rankings[i][:k]) / len(indexes), 3)

    everything = list(range(len(answers)))
    mrr = sum(
        1 / (rankings[i].index(answers[i]) + 1) for i in everything if answers[i] in rankings[i]
    )
    result = {
        "recall@1": recall(everything, 1),
        "recall@5": recall(everything, 5),
        "mrr": round(mrr / len(answers), 3),
    }

    for style in ("standard", "student", "hard"):
        indexes = [i for i, q in enumerate(QUESTIONS) if q.get("style", "standard") == style]
        if indexes:
            result[f"{style}_recall@1"] = recall(indexes, 1)
            result[f"{style}_recall@5"] = recall(indexes, 5)
    return result


class Embedder:
    def __init__(self, backend: str, model: str, batch_size: int) -> None:
        self.backend = backend
        self.model_name = model
        self.batch_size = batch_size
        self.query_prefix = (
            RETRIEVAL_QUERY_PREFIX if any(name in model.lower() for name in PREFIXED_MODELS) else ""
        )

        if backend == "fastembed":
            from fastembed import TextEmbedding

            self._model = TextEmbedding(model_name=model, cache_dir=str(MODEL_CACHE))
        else:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(model, device="cpu", cache_folder=str(MODEL_CACHE))

    def embed(self, texts: list[str]) -> np.ndarray:
        if self.backend == "fastembed":
            vectors = np.array(list(self._model.embed(texts, batch_size=self.batch_size)), dtype=np.float32)
        else:
            vectors = self._model.encode(texts, batch_size=self.batch_size, convert_to_numpy=True).astype(np.float32)
        return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)

    def embed_queries(self, texts: list[str]) -> np.ndarray:
        return self.embed([self.query_prefix + text for text in texts])


def benchmark_stores(vectors: np.ndarray, queries: np.ndarray, exact: list[list[int]], work: Path) -> dict:
    results: dict = {}
    dimension = vectors.shape[1]

    # sqlite-vec ---------------------------------------------------------------------
    import sqlite_vec

    db_file = work / "vectors.sqlite"
    connection = sqlite3.connect(db_file)
    connection.enable_load_extension(True)
    sqlite_vec.load(connection)
    connection.enable_load_extension(False)
    connection.execute(f"CREATE VIRTUAL TABLE vec_chunks USING vec0(embedding float[{dimension}])")

    start = time.perf_counter()
    connection.executemany(
        "INSERT INTO vec_chunks(rowid, embedding) VALUES (?, ?)",
        ((index, vector.tobytes()) for index, vector in enumerate(vectors)),
    )
    connection.commit()
    insert_seconds = time.perf_counter() - start

    latencies, overlaps = [], []
    for query, expected in zip(queries, exact):
        t0 = time.perf_counter()
        rows = connection.execute(
            "SELECT rowid FROM vec_chunks WHERE embedding MATCH ? AND k = ? ORDER BY distance",
            (query.tobytes(), TOP_CHUNKS),
        ).fetchall()
        latencies.append((time.perf_counter() - t0) * 1000)
        overlaps.append(len({r[0] for r in rows[:10]} & set(expected[:10])) / 10)
    connection.close()

    results["sqlite-vec"] = {
        "insert_seconds": round(insert_seconds, 2),
        "query_ms_median": round(statistics.median(latencies), 2),
        "query_ms_max": round(max(latencies), 2),
        "top10_agreement_with_exact": round(statistics.mean(overlaps), 3),
        "disk_mb": round(db_file.stat().st_size / 1024 / 1024, 1),
    }

    # ChromaDB --------------------------------------------------------------------------
    import chromadb

    chroma_dir = work / "chroma"
    client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = client.create_collection("chunks", metadata={"hnsw:space": "cosine"})

    start = time.perf_counter()
    batch = 5000
    for offset in range(0, len(vectors), batch):
        part = vectors[offset : offset + batch]
        collection.add(
            ids=[str(i) for i in range(offset, offset + len(part))],
            embeddings=part.tolist(),
        )
    insert_seconds = time.perf_counter() - start

    latencies, overlaps = [], []
    for query, expected in zip(queries, exact):
        t0 = time.perf_counter()
        found = collection.query(query_embeddings=[query.tolist()], n_results=TOP_CHUNKS)
        latencies.append((time.perf_counter() - t0) * 1000)
        ids = [int(i) for i in found["ids"][0]]
        overlaps.append(len(set(ids[:10]) & set(expected[:10])) / 10)

    results["chromadb"] = {
        "insert_seconds": round(insert_seconds, 2),
        "query_ms_median": round(statistics.median(latencies), 2),
        "query_ms_max": round(max(latencies), 2),
        "top10_agreement_with_exact": round(statistics.mean(overlaps), 3),
        "disk_mb": folder_mb(chroma_dir),
    }
    del collection, client
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("db_path", type=Path)
    parser.add_argument("results_dir", type=Path)
    parser.add_argument("--backend", choices=["fastembed", "sentence-transformers"], required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--stores", action="store_true")
    parser.add_argument("--batch", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--sample", type=int, default=0, help="speed-only run on N chunks")
    args = parser.parse_args()

    args.results_dir.mkdir(parents=True, exist_ok=True)
    texts, chunk_docs = load_chunks(args.db_path)

    if args.sample:
        # Speed-only run: an even spread of chunks; quality is not scored.
        step = max(1, len(texts) // args.sample)
        texts, chunk_docs = texts[::step][: args.sample], chunk_docs[::step][: args.sample]

    print(f"{len(texts)} chunks from {len(set(chunk_docs))} documents", flush=True)

    memory = PeakMemory()

    start = time.perf_counter()
    embedder = Embedder(args.backend, args.model, args.batch)
    load_seconds = time.perf_counter() - start
    print(f"Model loaded in {load_seconds:.1f}s", flush=True)

    start = time.perf_counter()
    cpu_start = time.process_time()
    vectors = embedder.embed(texts)
    embed_seconds = time.perf_counter() - start
    embed_cpu_seconds = time.process_time() - cpu_start
    print(f"Embedded in {embed_seconds:.1f}s ({len(texts) / embed_seconds:.0f} chunks/s)", flush=True)

    questions = [q["question"] for q in QUESTIONS]
    start = time.perf_counter()
    queries = embedder.embed_queries(questions)
    query_embed_ms = (time.perf_counter() - start) * 1000 / len(questions)

    peak_mb = memory.stop()

    # Exact (brute force) semantic ranking ----------------------------------------
    exact_orders = [list(np.argsort(-(vectors @ query))[: TOP_CHUNKS * 4]) for query in queries]
    semantic = [document_ranking(order, chunk_docs) for order in exact_orders]
    keyword = keyword_rankings(args.db_path)
    hybrid = [reciprocal_rank_fusion(s, k) for s, k in zip(semantic, keyword)]

    site_packages = Path(sys.prefix) / "Lib" / "site-packages"
    results = {
        "backend": args.backend,
        "model": args.model,
        "chunks": len(texts),
        "dimension": int(vectors.shape[1]),
        "model_load_seconds": round(load_seconds, 2),
        "batch_size": args.batch,
        "sample_only": bool(args.sample),
        "embed_seconds": round(embed_seconds, 1),
        # Wall time far above CPU time / cores means the machine slept or was busy.
        "embed_cpu_seconds": round(embed_cpu_seconds, 1),
        "chunks_per_second": round(len(texts) / embed_seconds, 1),
        "query_embed_ms": round(query_embed_ms, 1),
        "peak_memory_mb": peak_mb,
        "install_mb": folder_mb(site_packages),
        "model_files_mb": folder_mb(MODEL_CACHE) if MODEL_CACHE.exists() else None,
    }

    if not args.sample:
        results["quality"] = {
            "keyword_or": score(keyword),
            "semantic": score(semantic),
            "hybrid": score(hybrid),
        }

    if args.stores:
        work = Path(tempfile.mkdtemp(dir=args.results_dir))
        try:
            results["stores"] = benchmark_stores(vectors, queries, [list(o) for o in exact_orders], work)
        finally:
            shutil.rmtree(work, ignore_errors=True)

    suffix = f"_sample{args.sample}" if args.sample else ""
    name = f"embeddings_{args.backend}_{args.model.replace('/', '_')}{suffix}.json"
    (args.results_dir / name).write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
