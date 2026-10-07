"""Reads how busy the computer is, and how much the app itself uses."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import StrEnum

import psutil

MB = 1024 * 1024

# Below this much free memory, background work pauses to protect the system.
LOW_MEMORY_MB = 1024
# Background work resumes only once this much is free again (no flickering).
RECOVERED_MEMORY_MB = 1536
# Above this CPU load the computer counts as busy.
BUSY_CPU_PERCENT = 85.0


class Health(StrEnum):
    OK = "ok"
    BUSY = "busy"
    LOW_MEMORY = "low_memory"


@dataclass(frozen=True, slots=True)
class SystemSnapshot:
    app_memory_mb: float
    app_cpu_percent: float  # share of the whole computer
    system_cpu_percent: float
    memory_used_mb: float
    memory_total_mb: float
    memory_available_mb: float

    @property
    def memory_used_percent(self) -> float:
        return self.memory_used_mb / self.memory_total_mb * 100 if self.memory_total_mb else 0.0


def classify(snapshot: SystemSnapshot) -> Health:
    if snapshot.memory_available_mb < LOW_MEMORY_MB:
        return Health.LOW_MEMORY

    if snapshot.system_cpu_percent >= BUSY_CPU_PERCENT:
        return Health.BUSY

    return Health.OK


class SystemMonitor:
    """Takes snapshots of this process and the computer.

    CPU percentages are measured since the previous snapshot, so the
    first reading is 0 and later readings are averages over the interval.
    """

    def __init__(self) -> None:
        self._process = psutil.Process(os.getpid())
        self._cores = psutil.cpu_count() or 1
        # Start the CPU counters; the first call always returns 0.
        self._process.cpu_percent(None)
        psutil.cpu_percent(None)

    def snapshot(self) -> SystemSnapshot:
        memory = psutil.virtual_memory()

        return SystemSnapshot(
            app_memory_mb=self._process.memory_info().rss / MB,
            app_cpu_percent=min(100.0, self._process.cpu_percent(None) / self._cores),
            system_cpu_percent=psutil.cpu_percent(None),
            memory_used_mb=(memory.total - memory.available) / MB,
            memory_total_mb=memory.total / MB,
            memory_available_mb=memory.available / MB,
        )
