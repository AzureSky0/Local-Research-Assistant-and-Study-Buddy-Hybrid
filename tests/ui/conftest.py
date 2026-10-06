import os
import time
from collections.abc import Callable, Generator
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Run Qt without a visible window. Must be set before QApplication exists.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

import app.documents.orm  # noqa: E402, F401
import app.workspace.orm  # noqa: E402, F401
import app.knowledge.orm.keyword_index_schema  # noqa: E402, F401
from app.database.base import Base  # noqa: E402
from app.database.engine import configure_sqlite_connections  # noqa: E402
from app.ui.theme import apply_theme  # noqa: E402


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    application = QApplication.instance() or QApplication([])
    assert isinstance(application, QApplication)
    apply_theme(application)
    return application


@pytest.fixture
def session_factory(tmp_path: Path) -> Generator[Callable[[], Session], None, None]:
    """A file-based database usable from worker threads."""

    engine = create_engine(f"sqlite:///{(tmp_path / 'ui.db').as_posix()}")
    configure_sqlite_connections(engine)
    Base.metadata.create_all(engine)

    yield sessionmaker(bind=engine)

    engine.dispose()


def wait_until(condition: Callable[[], bool], timeout: float = 10.0) -> None:
    """Process Qt events until `condition` is true or the timeout passes."""

    deadline = time.monotonic() + timeout

    while not condition():
        if time.monotonic() > deadline:
            raise TimeoutError("Condition was not met in time")

        QCoreApplication.processEvents()
        time.sleep(0.01)

    for _ in range(5):
        QCoreApplication.processEvents()


PDF_HEADER = b"%PDF-1.4\n"


def make_library(folder: Path) -> Path:
    """Create a small folder of documents with one bad and one unsupported file."""

    (folder / "lectures").mkdir(parents=True)
    (folder / "paper.pdf").write_bytes(PDF_HEADER + b"paper")
    (folder / "lectures" / "notes.md").write_text("# Notes", encoding="utf-8")
    (folder / "checklist.txt").write_text("Revise", encoding="utf-8")
    (folder / "slides.pptx").write_bytes(b"PK")
    (folder / "renamed.pdf").write_text("not a pdf", encoding="utf-8")
    return folder
