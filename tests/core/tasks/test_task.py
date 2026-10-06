
from app.core.tasks.example import ExampleTask
from app.core.tasks.task_cancellation import TaskCancellationToken




def test_example_task_name() -> None:
    task = ExampleTask()

    assert task.name == "Example Task"


def test_example_task_execute() -> None:
    task = ExampleTask()
    cancellation_token = TaskCancellationToken()

    result = task.execute(cancellation_token,lambda progress: None,)

    assert result == "Task completed"