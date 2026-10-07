"""A deterministic embedder for tests: no model download, instant.

Words are hashed into buckets; a small synonym table puts related words
in the same bucket, which simulates "meaning" well enough to test that
search by meaning finds passages that share no words with the query.
"""

from __future__ import annotations

import re
import zlib
from collections.abc import Sequence

import numpy as np

from app.knowledge.embeddings.embedder import Embedder, EmbeddingModelUnavailableError
from app.knowledge.embeddings.embedding_models import EmbeddingModelSpec

FAKE_SPEC = EmbeddingModelSpec(
    model_id="test/fake-embedder",
    label="Fake",
    dimension=64,
    query_prefix="",
    batch_size=8,
    download_mb=0,
)

OTHER_FAKE_SPEC = EmbeddingModelSpec(
    model_id="test/other-fake-embedder",
    label="Other fake",
    dimension=32,
    query_prefix="",
    batch_size=8,
    download_mb=0,
)

SYNONYMS = {
    "optimizer": "adam",
    "optimiser": "adam",
    "teacher": "distil",
    "student": "distil",
    "distillation": "distil",
    "forger": "adversarial",
    "detective": "adversarial",
}


class FakeEmbedder(Embedder):
    def __init__(self, spec: EmbeddingModelSpec = FAKE_SPEC, unavailable: bool = False) -> None:
        super().__init__(spec)
        self.unavailable = unavailable
        self.calls = 0

    def load_model(self) -> None:
        if self.unavailable:
            raise EmbeddingModelUnavailableError("offline")

    def _embed(self, texts: Sequence[str]) -> np.ndarray:
        self.load_model()
        self.calls += 1
        vectors = np.zeros((len(texts), self.spec.dimension), dtype=np.float32)

        for row, text in enumerate(texts):
            for word in re.findall(r"\w+", text.lower()):
                word = SYNONYMS.get(word, word)
                bucket = zlib.crc32(word.encode()) % self.spec.dimension
                vectors[row, bucket] += 1.0

        return vectors
