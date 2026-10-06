from uuid import UUID

from app.core.tasks.task_cancellation import TaskCancellationToken
from app.core.tasks.task_handle import TaskHandle
from app.core.tasks.task_manager import TaskManager
from app.core.tasks.task_status import TaskStatus


def create_handle() -> TaskHandle:
    return TaskHandle(
        cancellation_token=TaskCancellationToken(),
    )


def test_register_returns_task_id():
    manager = TaskManager()
    handle = create_handle()

    task_id = manager.register(handle)

    assert isinstance(task_id, UUID)


def test_registered_task_can_be_retrieved():
    manager = TaskManager()
    handle = create_handle()

    task_id = manager.register(handle)

    assert manager.get(task_id) is handle


def test_get_returns_none_for_unknown_task():
    manager = TaskManager()

    task_id = UUID("00000000-0000-0000-0000-000000000000")

    assert manager.get(task_id) is None


def test_list_tasks_returns_registered_tasks():
    manager = TaskManager()

    first_handle = create_handle()
    second_handle = create_handle()

    first_id = manager.register(first_handle)
    second_id = manager.register(second_handle)

    tasks = manager.list_tasks()

    assert tasks == {
        first_id: first_handle,
        second_id: second_handle,
    }


def test_list_tasks_returns_copy():
    manager = TaskManager()
    handle = create_handle()

    task_id = manager.register(handle)

    tasks = manager.list_tasks()
    tasks.clear()

    assert manager.get(task_id) is handle


def test_remove_existing_task():
    manager = TaskManager()
    handle = create_handle()

    task_id = manager.register(handle)

    assert manager.remove(task_id) is True
    assert manager.get(task_id) is None


def test_remove_unknown_task_returns_false():
    manager = TaskManager()

    task_id = UUID("00000000-0000-0000-0000-000000000000")

    assert manager.remove(task_id) is False

def test_cleanup_completed_removes_completed_tasks():
    manager = TaskManager()

    handle = create_handle()
    task_id = manager.register(handle)

    handle.update_status(TaskStatus.COMPLETED)

    removed = manager.cleanup_completed()

    assert removed == 1
    assert manager.get(task_id) is None


def test_cleanup_completed_removes_failed_tasks():
    manager = TaskManager()

    handle = create_handle()
    task_id = manager.register(handle)

    handle.update_status(TaskStatus.FAILED)

    removed = manager.cleanup_completed()

    assert removed == 1
    assert manager.get(task_id) is None


def test_cleanup_completed_removes_cancelled_tasks():
    manager = TaskManager()

    handle = create_handle()
    task_id = manager.register(handle)

    handle.update_status(TaskStatus.CANCELLED)

    removed = manager.cleanup_completed()

    assert removed == 1
    assert manager.get(task_id) is None


def test_cleanup_completed_keeps_pending_tasks():
    manager = TaskManager()

    handle = create_handle()
    task_id = manager.register(handle)

    removed = manager.cleanup_completed()

    assert removed == 0
    assert manager.get(task_id) is handle


def test_cleanup_completed_keeps_running_tasks():
    manager = TaskManager()

    handle = create_handle()
    task_id = manager.register(handle)

    handle.update_status(TaskStatus.RUNNING)

    removed = manager.cleanup_completed()

    assert removed == 0
    assert manager.get(task_id) is handle


def test_cleanup_completed_returns_number_of_removed_tasks():
    manager = TaskManager()

    completed = create_handle()
    failed = create_handle()
    running = create_handle()

    manager.register(completed)
    manager.register(failed)
    running_id = manager.register(running)

    completed.update_status(TaskStatus.COMPLETED)
    failed.update_status(TaskStatus.FAILED)
    running.update_status(TaskStatus.RUNNING)

    removed = manager.cleanup_completed()

    assert removed == 2
    assert manager.get(running_id) is running