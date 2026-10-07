"""Embedding models per computer profile (Decision 035)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.computer_profile import ComputerProfile

# BGE and Arctic models expect this instruction in front of search queries.
RETRIEVAL_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


@dataclass(frozen=True, slots=True)
class EmbeddingModelSpec:
    """A model that turns text into vectors for search by meaning."""

    model_id: str  # fastembed model name
    label: str  # shown to users
    dimension: int
    query_prefix: str
    batch_size: int
    download_mb: int

    @property
    def key(self) -> str:
        """Safe identifier for table names, for example arctic_embed_xs."""
        name = self.model_id.rsplit("/", 1)[-1].lower()
        name = name.removeprefix("snowflake-")
        return re.sub(r"[^a-z0-9]+", "_", name).strip("_")


ARCTIC_EMBED_XS = EmbeddingModelSpec(
    model_id="snowflake/snowflake-arctic-embed-xs",
    label="Arctic Embed XS",
    dimension=384,
    query_prefix=RETRIEVAL_QUERY_PREFIX,
    batch_size=16,
    download_mb=90,
)

POTION_RETRIEVAL_32M = EmbeddingModelSpec(
    model_id="minishlab/potion-retrieval-32M",
    label="Potion Retrieval 32M",
    dimension=512,
    query_prefix="",
    batch_size=64,
    download_mb=130,
)

PROFILE_MODELS: dict[ComputerProfile, EmbeddingModelSpec] = {
    ComputerProfile.STANDARD: ARCTIC_EMBED_XS,
    ComputerProfile.LIGHT: POTION_RETRIEVAL_32M,
}

ALL_MODELS = list(PROFILE_MODELS.values())


def model_for_profile(profile: ComputerProfile) -> EmbeddingModelSpec:
    return PROFILE_MODELS[profile]
