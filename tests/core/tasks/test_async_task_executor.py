from __future__ import annotations

import time
from app.core.tasks.async_task_executor import AsyncTaskExecutor
from app.core.tasks.example import ExampleTask
from app.core.tasks.task import Task
from app.core.tasks.task_status import TaskStatus
from app.core.tasks.task_cancellation import TaskCancellationToken
from app.core.tasks.task_progress import TaskProgress


class SlowTask(Task):
    """Task used to verify background execution."""

    @property
    def name(self) -> str:
        return "Slow Task"

    def execute(self,cancellation_token: TaskCancellationToken,progress_callback) -> str:
        time.sleep(0.1)
        return "Slow task completed"


class FailingTask(Task):
    """Task used to test background failure handling."""

    @property
    def name(self) -> str:
        return "Failing Task"

    def execute(
        self,
        cancellation_token: TaskCancellationToken,
        progress_callback,
    ) -> str:
        raise ValueError("Background task failed")


def test_submit_returns_future() -> None:
    executor = AsyncTaskExecutor(max_workers=2)

    try:
        handle = executor.submit(ExampleTask())

        result = handle.result(timeout=2)

        assert result.status is TaskStatus.COMPLETED
        assert result.value == "Task completed"

    finally:
        executor.shutdown()


def test_task_runs_in_background() -> None:
    executor = AsyncTaskExecutor(max_workers=1)

    try:
        handle = executor.submit(SlowTask())

        assert not handle.done

        result = handle.result(timeout=2)

        assert result.status is TaskStatus.COMPLETED
        assert result.value == "Slow task completed"

    finally:
        executor.shutdown()


def test_background_task_failure_is_captured() -> None:
    executor = AsyncTaskExecutor(max_workers=1)

    try:
        handle = executor.submit(FailingTask())

        result = handle.result(timeout=2)

        assert result.status is TaskStatus.FAILED
        assert result.value is None
        assert isinstance(result.error, ValueError)
        assert str(result.error) == "Background task failed"

    finally:
        executor.shutdown()

class CancellableTask(Task):
    """Task that waits for cancellation."""

    @property
    def name(self) -> str:
        return "Cancellable Task"

    def execute(
        self,
        cancellation_token: TaskCancellationToken,
        progress_callback,
    ) -> str:
        while not cancellation_token.is_cancelled:
            time.sleep(0.01)

        cancellation_token.throw_if_cancelled()

        return "Should never complete"


def test_running_task_can_be_cancelled() -> None:
    executor = AsyncTaskExecutor(max_workers=1)

    try:
        handle = executor.submit(CancellableTask())

        time.sleep(0.05)

        assert handle.done is False
        assert handle.is_cancelled is False

        handle.cancel()

        assert handle.is_cancelled is True

        result = handle.result(timeout=2)

        assert result.status is TaskStatus.CANCELLED
        assert result.value is None
        assert result.error is None
        assert result.status == TaskStatus.CANCELLED
        assert handle.status == TaskStatus.CANCELLED

    finally:
        executor.shutdown()

def test_handle_reports_completion() -> None:
    executor = AsyncTaskExecutor(max_workers=1)

    try:
        handle = executor.submit(ExampleTask())

        result = handle.result(timeout=2)

        assert result.status is TaskStatus.COMPLETED
        assert handle.done is True

    finally:
        executor.shutdown()


def test_task_progress_is_forwarded() -> None:
    executor = AsyncTaskExecutor(max_workers=1)
    progress_updates: list[TaskProgress] = []

    class ProgressTask(Task):
        @property
        def name(self) -> str:
            return "Progress Task"

        def execute(
            self,
            cancellation_token: TaskCancellationToken,
            progress_callback,
        ) -> str:
            progress_callback(TaskProgress(10, 100, "Starting"))
            progress_callback(TaskProgress(50, 100, "Processing"))
            progress_callback(TaskProgress(100, 100, "Complete"))

            return "Progress task completed"

    try:
        handle = executor.submit(
            ProgressTask(),
            progress_callback=lambda progress: progress_updates.append(progress),
        )

        result = handle.result(timeout=2)

        assert result.status is TaskStatus.COMPLETED
        assert result.value == "Progress task completed"

        assert progress_updates == [
            TaskProgress(10, 100, "Starting"),
            TaskProgress(50, 100, "Processing"),
            TaskProgress(100, 100, "Complete"),
        ]

    finally:
        executor.shutdown()

def test_task_status_becomes_completed():
    executor = AsyncTaskExecutor(max_workers=1)

    try:
        handle = executor.submit(ExampleTask())

        result = handle.result(timeout=2)

        assert result.status == TaskStatus.COMPLETED
        assert handle.status == TaskStatus.COMPLETED
    finally:
        executor.shutdown()

def test_task_status_becomes_failed():
    class FailingTask(Task):
        @property
        def name(self) -> str:
            return "Failing Task"

        def execute(
            self,
            cancellation_token: TaskCancellationToken,
            progress_callback,
        ):
            raise ValueError("Something went wrong")

    executor = AsyncTaskExecutor(max_workers=1)

    try:
        handle = executor.submit(FailingTask())

        result = handle.result(timeout=2)

        assert result.status == TaskStatus.FAILED
        assert handle.status == TaskStatus.FAILED
    finally:
        executor.shutdown()


def test_task_cancelled_before_start_does_not_run() -> None:
    executor = AsyncTaskExecutor(max_workers=1)
    executed: list[str] = []

    class RecordingTask(Task):
        @property
        def name(self) -> str:
            return "Recording Task"

        def execute(
            self,
            cancellation_token: TaskCancellationToken,
            progress_callback,
        ) -> str:
            executed.append(self.name)
            return "Recording task completed"

    try:
        blocking_handle = executor.submit(CancellableTask())
        queued_handle = executor.submit(RecordingTask())

        queued_handle.cancel()
        blocking_handle.cancel()

        result = queued_handle.result(timeout=2)

        assert result.status is TaskStatus.CANCELLED
        assert queued_handle.status == TaskStatus.CANCELLED
        assert executed == []

    finally:
        executor.shutdown()
