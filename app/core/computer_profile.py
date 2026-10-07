"""Detects what this computer can comfortably run (Decision 037).

The computer profile is the ceiling for local models: Light machines use
the fastest components, Standard machines use better but heavier ones.
It is detected automatically and can be overridden in Settings.
"""

from __future__ import annotations

import ctypes
import os
import subprocess
import sys
from enum import StrEnum

# Machines with less memory than this get the Light profile.
STANDARD_PROFILE_MIN_RAM_GB = 12


class ComputerProfile(StrEnum):
    LIGHT = "light"
    STANDARD = "standard"

    @property
    def label(self) -> str:
        return self.value.capitalize()


def total_memory_gb() -> float | None:
    """Total physical memory in GB, or None if it cannot be determined."""

    try:
        if sys.platform == "win32":
            return _windows_total_memory() / 1024**3

        if sys.platform == "darwin":
            output = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            ).stdout
            return int(output.strip()) / 1024**3

        pages = os.sysconf("SC_PHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
        return pages * page_size / 1024**3

    except (OSError, ValueError, subprocess.SubprocessError, AttributeError):
        return None


def _windows_total_memory() -> int:
    class MemoryStatus(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    status = MemoryStatus()
    status.dwLength = ctypes.sizeof(MemoryStatus)

    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):  # type: ignore[attr-defined]
        raise OSError("GlobalMemoryStatusEx failed")

    return int(status.ullTotalPhys)


def detect_profile(memory_gb: float | None = None) -> ComputerProfile:
    """Choose a profile from the amount of memory.

    When memory cannot be determined, Light is the safe choice.
    """

    if memory_gb is None:
        memory_gb = total_memory_gb()

    if memory_gb is not None and memory_gb >= STANDARD_PROFILE_MIN_RAM_GB:
        return ComputerProfile.STANDARD

    return ComputerProfile.LIGHT
