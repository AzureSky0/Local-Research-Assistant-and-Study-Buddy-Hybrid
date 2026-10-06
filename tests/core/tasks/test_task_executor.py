from app.core.tasks import TaskExecutor
from app.core.tasks.example import ExampleTask
from app.core.tasks.task import Task
from app.core.tasks.task_status import TaskStatus
from app.core.tasks.task import TaskProgressCallback
from app.core.tasks.task_cancellation import (
    TaskCancellationToken,
    TaskCancelledError,
)


class FailingTask(Task):
    """Task used to test executor failure handling."""

    @property
    def name(self) -> str:
        return "Failing Task"

    def execute(self,cancellation_token: TaskCancellationToken,progress_callback: TaskProgressCallback,) -> str:
        raise ValueError("Task failed")


def test_executor_returns_completed_result() -> None:
    executor = TaskExecutor()
    task = ExampleTask()

    result = executor.execute(task)

    assert result.status is TaskStatus.COMPLETED
    assert result.value == "Task completed"
    assert result.error is None


def test_executor_returns_failed_result() -> None:
    executor = TaskExecutor()
    task = FailingTask()

    result = executor.execute(task)

    assert result.status is TaskStatus.FAILED
    assert result.value is None
    assert isinstance(result.error, ValueError)
    assert str(result.error) == "Task failed"


class CancelledTask(Task):
    """Task used to test executor cancellation handling."""

    @property
    def name(self) -> str:
        return "Cancelled Task"

    def execute(
        self,
        cancellation_token: TaskCancellationToken,
        progress_callback: TaskProgressCallback,
    ) -> str:
        raise TaskCancelledError


def test_executor_returns_cancelled_result() -> None:
    executor = TaskExecutor()

    result = executor.execute(CancelledTask())

    assert result.status is TaskStatus.CANCELLED
    assert result.value is None
    assert result.error is None
