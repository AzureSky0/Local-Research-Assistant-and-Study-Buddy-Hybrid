"""Turns text into normalized vectors with a local model."""

from __future__ import annotations

import logging
import threading
from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from app.knowledge.embeddings.embedding_models import EmbeddingModelSpec

if TYPE_CHECKING:
    from fastembed import TextEmbedding

logger = logging.getLogger(__name__)

# The background worker and search each load the model; on the first run
# only one of them should download it while the other waits.
_LOAD_LOCK = threading.Lock()


class EmbeddingModelUnavailableError(RuntimeError):
    """The model could not be loaded, usually because it has never been
    downloaded and the computer is offline. The message is shown to users."""


class Embedder(ABC):
    """Embeds passages and search queries for one model."""

    def __init__(self, spec: EmbeddingModelSpec) -> None:
        self.spec = spec

    def load_model(self) -> None:
        """Load the model now (downloading it the first time), instead of on first use."""

    @abstractmethod
    def _embed(self, texts: Sequence[str]) -> np.ndarray:
        """Raw vectors, one row per text."""

    def embed_passages(self, texts: Sequence[str]) -> np.ndarray:
        return _normalize(self._embed(texts))

    def embed_query(self, text: str) -> np.ndarray:
        return _normalize(self._embed([self.spec.query_prefix + text]))[0]


class FastEmbedEmbedder(Embedder):
    """Runs a fastembed (ONNX) model on the CPU, fully offline once downloaded.

    The model is loaded on first use; the first load downloads it into
    the application's models folder.
    """

    def __init__(self, spec: EmbeddingModelSpec, cache_dir: Path) -> None:
        super().__init__(spec)
        self._cache_dir = cache_dir
        self._model: TextEmbedding | None = None

    def load_model(self) -> None:
        if self._model is not None:
            return

        try:
            from fastembed import TextEmbedding

            with _LOAD_LOCK:
                self._model = TextEmbedding(
                    model_name=self.spec.model_id, cache_dir=str(self._cache_dir)
                )
        except Exception as error:
            logger.warning("Could not load embedding model %s: %s", self.spec.model_id, error)
            raise EmbeddingModelUnavailableError(
                f"The search model ({self.spec.label}, about {self.spec.download_mb} MB) "
                "could not be loaded. It is downloaded once, the first time it is needed — "
                "check the internet connection and try again. Word search works normally."
            ) from error

    def _embed(self, texts: Sequence[str]) -> np.ndarray:
        self.load_model()
        assert self._model is not None
        vectors = self._model.embed(list(texts), batch_size=self.spec.batch_size)
        return np.asarray(list(vectors), dtype=np.float32)


def _normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (vectors / norms).astype(np.float32)
