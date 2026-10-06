from app.core.tasks.task_progress import TaskProgress


def test_progress_starts_at_zero() -> None:
    progress = TaskProgress(
        current=0,
        total=10,
    )

    assert progress.current == 0
    assert progress.total == 10
    assert progress.percentage == 0
    assert progress.message == ""


def test_progress_calculates_percentage() -> None:
    progress = TaskProgress(
        current=5,
        total=10,
    )

    assert progress.percentage == 50


def test_progress_reaches_one_hundred_percent() -> None:
    progress = TaskProgress(
        current=10,
        total=10,
    )

    assert progress.percentage == 100


def test_progress_supports_message() -> None:
    progress = TaskProgress(
        current=3,
        total=10,
        message="Processing document",
    )

    assert progress.message == "Processing document"
    assert progress.percentage == 30


def test_zero_total_has_zero_percentage() -> None:
    progress = TaskProgress(
        current=0,
        total=0,
    )

    assert progress.percentage == 0


def test_negative_total_is_rejected() -> None:
    try:
        TaskProgress(
            current=0,
            total=-1,
        )
    except ValueError as error:
        assert str(error) == "total cannot be negative"
    else:
        raise AssertionError(
            "Expected ValueError"
        )


def test_negative_current_is_rejected() -> None:
    try:
        TaskProgress(
            current=-1,
            total=10,
        )
    except ValueError as error:
        assert str(error) == "current cannot be negative"
    else:
        raise AssertionError(
            "Expected ValueError"
        )


def test_current_greater_than_total_is_rejected() -> None:
    try:
        TaskProgress(
            current=11,
            total=10,
        )
    except ValueError as error:
        assert str(error) == (
            "current cannot be greater than total"
        )
    else:
        raise AssertionError(
            "Expected ValueError"
        )