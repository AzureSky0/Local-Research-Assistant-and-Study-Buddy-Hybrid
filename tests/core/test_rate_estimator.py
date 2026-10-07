from app.core.rate_estimator import MIN_MEASURED_SECONDS, RateEstimator


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_estimate_follows_the_pace() -> None:
    clock = Clock()
    pace = RateEstimator(clock=clock)

    pace.record(0)
    clock.now = 20
    pace.record(40)  # 2 per second

    assert pace.seconds_left(100) == 50


def test_no_estimate_until_enough_is_measured() -> None:
    clock = Clock()
    pace = RateEstimator(clock=clock)

    assert pace.seconds_left(10) is None
    pace.record(0)
    clock.now = MIN_MEASURED_SECONDS / 2
    pace.record(5)
    assert pace.seconds_left(10) is None


def test_no_estimate_without_progress() -> None:
    clock = Clock()
    pace = RateEstimator(clock=clock)
    pace.record(10)
    clock.now = 30
    pace.record(10)

    assert pace.seconds_left(10) is None


def test_only_recent_pace_counts() -> None:
    clock = Clock()
    pace = RateEstimator(window_seconds=60, clock=clock)

    # Slow at first (1 per 10 s)...
    for step in range(10):
        clock.now = step * 10
        pace.record(step)
    # ...then fast (1 per second).
    for step in range(1, 121):
        clock.now = 90 + step
        pace.record(9 + step)

    left = pace.seconds_left(60)
    assert left is not None and 55 <= left <= 65


def test_count_going_backwards_starts_again() -> None:
    clock = Clock()
    pace = RateEstimator(clock=clock)
    pace.record(0)
    clock.now = 20
    pace.record(100)

    clock.now = 21
    pace.record(0)

    assert pace.seconds_left(10) is None


def test_waiting_before_the_first_progress_is_not_counted() -> None:
    clock = Clock()
    pace = RateEstimator(clock=clock)

    # 30 s of waiting (a model download), then 10 per second.
    for second in range(0, 31, 5):
        clock.now = second
        pace.record(0)
    for step in range(1, 5):
        clock.now = 30 + step * 5
        pace.record(step * 50)

    assert pace.seconds_left(100) == 10
