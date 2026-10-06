from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class DocumentDiscoveryResult:
    """Files found while scanning a folder for documents."""

    supported_files: list[Path] = field(default_factory=list)
    unsupported_files: list[Path] = field(default_factory=list)
    inaccessible_paths: list[Path] = field(default_factory=list)
