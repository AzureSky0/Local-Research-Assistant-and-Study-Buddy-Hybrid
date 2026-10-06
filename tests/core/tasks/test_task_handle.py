from app.core.tasks.task_cancellation import TaskCancellationToken
from app.core.tasks.task_handle import TaskHandle

from app.core.tasks.task_status import TaskStatus

def test_handle_is_not_cancelled_initially() -> None:
    token = TaskCancellationToken()
    handle = TaskHandle(token)

    assert handle.is_cancelled is False


def test_handle_requests_cancellation() -> None:
    token = TaskCancellationToken()
    handle = TaskHandle(token)

    handle.cancel()

    assert handle.is_cancelled is True
    assert token.is_cancelled is True


def test_handle_can_be_cancelled_multiple_times() -> None:
    token = TaskCancellationToken()
    handle = TaskHandle(token)

    handle.cancel()
    handle.cancel()

    assert handle.is_cancelled is True
    assert token.is_cancelled is True

def test_handle_starts_as_pending():
    token = TaskCancellationToken()
    handle = TaskHandle(token)

    assert handle.status == TaskStatus.PENDING


def test_handle_status_can_be_updated():
    token = TaskCancellationToken()
    handle = TaskHandle(token)

    handle.update_status(TaskStatus.RUNNING)

    assert handle.status == TaskStatus.RUNNING