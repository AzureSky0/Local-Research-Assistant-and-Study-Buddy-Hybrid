"""Estimate how long background work has left from its recent pace."""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable

# Only the recent pace counts: it changes when the computer gets busy or
# when large documents give way to small ones.
WINDOW_SECONDS = 120.0

# Too early to say anything sensible before this much has been measured.
MIN_MEASURED_SECONDS = 10.0


class RateEstimator:
    """Feed it a running count of finished items; it estimates the time left."""

    def __init__(
        self,
        window_seconds: float = WINDOW_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._window = window_seconds
        self._clock = clock
        self._samples: deque[tuple[float, int]] = deque()

    def record(self, finished: int) -> None:
        now = self._clock()

        # The count went backwards (for example the search model changed
        # and everything starts again): the old pace means nothing.
        if self._samples and finished < self._samples[-1][1]:
            self._samples.clear()

        # Measure from the first progress: waiting before it (for example
        # while a model downloads) is not the pace of the work.
        if self._samples and self._samples[0][1] == finished:
            self._samples.clear()

        self._samples.append((now, finished))
        while len(self._samples) > 2 and now - self._samples[1][0] >= self._window:
            self._samples.popleft()

    def reset(self) -> None:
        """Forget the pace, for example after a pause."""
        self._samples.clear()

    def seconds_left(self, remaining: int) -> float | None:
        if remaining <= 0 or len(self._samples) < 2:
            return None

        (start, first), (end, last) = self._samples[0], self._samples[-1]
        measured = end - start
        if measured < MIN_MEASURED_SECONDS or last <= first:
            return None

        return remaining * measured / (last - first)
