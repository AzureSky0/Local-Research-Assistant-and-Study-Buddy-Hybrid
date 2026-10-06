from app.core.tasks.task_cancellation import (
    TaskCancellationToken,
    TaskCancelledError,
)


def test_token_is_not_cancelled_initially() -> None:
    token = TaskCancellationToken()

    assert token.is_cancelled is False


def test_cancel_marks_token_as_cancelled() -> None:
    token = TaskCancellationToken()

    token.cancel()

    assert token.is_cancelled is True


def test_throw_if_cancelled_does_nothing_when_not_cancelled() -> None:
    token = TaskCancellationToken()

    token.throw_if_cancelled()


def test_throw_if_cancelled_raises_after_cancellation() -> None:
    token = TaskCancellationToken()

    token.cancel()

    try:
        token.throw_if_cancelled()
    except TaskCancelledError:
        pass
    else:
        raise AssertionError(
            "Expected TaskCancelledError"
        )