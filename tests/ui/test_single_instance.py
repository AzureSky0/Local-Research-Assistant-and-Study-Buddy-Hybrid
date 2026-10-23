from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.core.single_instance import SingleInstance
from tests.ui.conftest import wait_until


def test_only_one_copy_runs_per_data_folder(qapp: QApplication, tmp_path: Path) -> None:
    first = SingleInstance(tmp_path)
    second = SingleInstance(tmp_path)

    assert first.acquire()
    assert not second.acquire()

    first.release()


def test_second_copy_brings_the_first_to_the_front(qapp: QApplication, tmp_path: Path) -> None:
    first = SingleInstance(tmp_path)
    assert first.acquire()
    requests: list[bool] = []
    first.activation_requested.connect(lambda: requests.append(True))

    second = SingleInstance(tmp_path)
    assert not second.acquire()
    assert second.ask_running_copy_to_show()

    wait_until(lambda: bool(requests))
    first.release()


def test_lock_is_free_again_after_the_first_copy_closes(qapp: QApplication, tmp_path: Path) -> None:
    first = SingleInstance(tmp_path)
    assert first.acquire()
    first.release()

    again = SingleInstance(tmp_path)
    assert again.acquire()
    again.release()


def test_different_data_folders_do_not_block_each_other(qapp: QApplication, tmp_path: Path) -> None:
    one = SingleInstance(tmp_path / "one")
    other = SingleInstance(tmp_path / "other")
    (tmp_path / "one").mkdir()
    (tmp_path / "other").mkdir()

    assert one.acquire()
    assert other.acquire()

    one.release()
    other.release()
