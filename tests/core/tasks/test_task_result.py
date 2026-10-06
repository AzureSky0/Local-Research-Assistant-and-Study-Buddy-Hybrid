from app.core.tasks import TaskResult, TaskStatus


def test_task_status_values() -> None:
    assert TaskStatus.PENDING.value == "pending"
    assert TaskStatus.RUNNING.value == "running"
    assert TaskStatus.COMPLETED.value == "completed"
    assert TaskStatus.FAILED.value == "failed"
    assert TaskStatus.CANCELLED.value == "cancelled"


def test_successful_task_result() -> None:
    result = TaskResult(
        status=TaskStatus.COMPLETED,
        value="Task completed",
    )

    assert result.status is TaskStatus.COMPLETED
    assert result.value == "Task completed"
    assert result.error is None


def test_failed_task_result() -> None:
    error = ValueError("Something went wrong")

    result = TaskResult(
        status=TaskStatus.FAILED,
        error=error,
    )

    assert result.status is TaskStatus.FAILED
    assert result.value is None
    assert result.error is error


def test_cancelled_task_result() -> None:
    result = TaskResult(
        status=TaskStatus.CANCELLED,
    )

    assert result.status is TaskStatus.CANCELLED
    assert result.value is None
    assert result.error is None