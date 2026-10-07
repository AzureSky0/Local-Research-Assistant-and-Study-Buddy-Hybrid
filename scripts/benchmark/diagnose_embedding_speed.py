"""Diagnose embedding speed differences on a sample of benchmark chunks.

Usage (ONNX benchmark environment):
    python scripts/benchmark/diagnose_embedding_speed.py DB_PATH [SAMPLE_SIZE]
"""

from __future__ import annotations

import os
import platform
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
MODEL_CACHE = HERE.parent.parent / "data" / "benchmark" / "models"


def sample_chunks(db_path: str, size: int) -> list[str]:
    connection = sqlite3.connect(db_path)
    rows = connection.execute(
        "SELECT text FROM chunks ORDER BY rowid LIMIT ?", (size,)
    ).fetchall()
    connection.close()
    return [row[0] for row in rows]


def timed(label: str, function, texts: list[str]) -> float:  # type: ignore[no-untyped-def]
    function(texts[:8])  # warm up
    start = time.perf_counter()
    vectors = function(texts)
    seconds = time.perf_counter() - start
    rate = len(texts) / seconds
    print(f"{label:58} {rate:7.1f} chunks/s   dim={np.asarray(vectors).shape[-1]}", flush=True)
    return rate


def fastembed_runner(model: str, batch_size: int):  # type: ignore[no-untyped-def]
    from fastembed import TextEmbedding

    embedder = TextEmbedding(model_name=model, cache_dir=str(MODEL_CACHE))
    return lambda texts: list(embedder.embed(texts, batch_size=batch_size))


def onnx_fp32_runner(repo: str, file: str, max_length: int = 512):  # type: ignore[no-untyped-def]
    """Run a full-precision ONNX export directly with onnxruntime."""
    import onnxruntime as ort
    from huggingface_hub import hf_hub_download
    from tokenizers import Tokenizer

    model_path = hf_hub_download(repo, file, cache_dir=str(MODEL_CACHE))
    tokenizer = Tokenizer.from_file(hf_hub_download(repo, "tokenizer.json", cache_dir=str(MODEL_CACHE)))
    tokenizer.enable_truncation(max_length=max_length)
    tokenizer.enable_padding()

    session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
    input_names = {i.name for i in session.get_inputs()}

    def run(texts: list[str]) -> np.ndarray:
        outputs = []
        for start in range(0, len(texts), 32):
            encoded = tokenizer.encode_batch(texts[start : start + 32])
            ids = np.array([e.ids for e in encoded], dtype=np.int64)
            mask = np.array([e.attention_mask for e in encoded], dtype=np.int64)
            feeds = {"input_ids": ids, "attention_mask": mask}
            if "token_type_ids" in input_names:
                feeds["token_type_ids"] = np.zeros_like(ids)
            hidden = session.run(None, feeds)[0]
            outputs.append(hidden[:, 0])  # CLS pooling, as BGE uses
        return np.concatenate(outputs)

    return run


def main() -> None:
    db_path = sys.argv[1]
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    texts = sample_chunks(db_path, size)

    print(f"CPU: {platform.processor()} | logical cores: {os.cpu_count()}")
    import onnxruntime as ort

    print(f"onnxruntime {ort.__version__}, {len(texts)} chunks, "
          f"avg {np.mean([len(t.split()) for t in texts]):.0f} words\n")

    from fastembed import TextEmbedding

    for description in TextEmbedding.list_supported_models():
        if description["model"] in ("BAAI/bge-small-en-v1.5", "sentence-transformers/all-MiniLM-L6-v2"):
            print(f"fastembed {description['model']}: source {description.get('sources')}, "
                  f"file {description.get('model_file')}")
    print()

    timed("fastembed bge-small (as benchmarked, batch 64)", fastembed_runner("BAAI/bge-small-en-v1.5", 64), texts)
    timed("fastembed bge-small, batch 8", fastembed_runner("BAAI/bge-small-en-v1.5", 8), texts)
    timed("fastembed all-MiniLM-L6-v2, batch 64", fastembed_runner("sentence-transformers/all-MiniLM-L6-v2", 64), texts)
    timed("onnxruntime + full-precision bge-small (BAAI/onnx/model.onnx)",
          onnx_fp32_runner("BAAI/bge-small-en-v1.5", "onnx/model.onnx"), texts)


if __name__ == "__main__":
    main()
