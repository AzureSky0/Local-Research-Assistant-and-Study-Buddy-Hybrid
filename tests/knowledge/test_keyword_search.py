from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.documents.domain import Document, DocumentProcessingStatus
from app.documents.repository.document_page_repository import DocumentPageRepository
from app.documents.services.document_service import DocumentService
from app.knowledge.dto.search_results import HIGHLIGHT_END, HIGHLIGHT_START
from app.knowledge.services.keyword_search_service import KeywordSearchService
from app.knowledge.services.search_query import build_match_query
from app.workspace.dto.workspace_create import WorkspaceCreateDTO
from app.workspace.services.workspace_service import WorkspaceService

# Query building ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("typed", "expected"),
    [
        ("gradient", '"gradient"*'),
        ("gradient ", '"gradient"'),
        ("gradient descent", '"gradient" "descent"*'),
        ('"learning rate"', '"learning rate"'),
        ('"learning rate" sched', '"learning rate" "sched"*'),
        ('"unfinished phrase', '"unfinished phrase"'),
        ("state-of-the-art", '"state" "of" "the" "art"*'),
        ("AND OR NOT NEAR", '"AND" "OR" "NOT" "NEAR"*'),
        ("café", '"café"*'),
        ("   ", None),
        ("*** ()", None),
    ],
)
def test_build_match_query(typed: str, expected: str | None) -> None:
    assert build_match_query(typed) == expected


# Search --------------------------------------------------------------------------


def add_document(
    session: Session,
    workspace_id: str,
    file_name: str,
    pages: list[str],
) -> Document:
    document = DocumentService(session).create_document(
        Document(
            id=str(uuid4()),
            workspace_id=workspace_id,
            file_name=file_name,
            original_path=f"D:/papers/{file_name}",
            file_size=100,
            checksum=str(uuid4()),
            file_type="pdf",
            imported_at=datetime.now(UTC),
            processing_status=DocumentProcessingStatus.READY,
        )
    )

    DocumentPageRepository(session).add_pages(
        document.id,
        [(number, page) for number, page in enumerate(pages, start=1)],
    )
    KeywordSearchService(session).index_document(document.id)
    session.commit()

    return document


@pytest.fixture
def search(session: Session) -> KeywordSearchService:
    return KeywordSearchService(session)


def test_finds_pages_with_page_numbers_and_highlights(
    session: Session, workspace_id: str, search: KeywordSearchService
) -> None:
    add_document(
        session,
        workspace_id,
        "optimization.pdf",
        ["Introduction", "Gradient descent takes small steps downhill."],
    )

    results = search.search(workspace_id, "gradient descent")

    assert len(results.passages) == 1
    passage = results.passages[0]
    assert passage.file_name == "optimization.pdf"
    assert passage.page_number == 2
    assert f"{HIGHLIGHT_START}Gradient{HIGHLIGHT_END}" in passage.snippet
    assert f"{HIGHLIGHT_START}descent{HIGHLIGHT_END}" in passage.snippet


def test_matches_word_forms_accents_and_prefixes(
    session: Session, workspace_id: str, search: KeywordSearchService
) -> None:
    add_document(session, workspace_id, "notes.pdf", ["The learning rate matters. Café notes."])

    assert search.search(workspace_id, "learn").passages
    assert search.search(workspace_id, "learns").passages
    assert search.search(workspace_id, "cafe").passages
    assert search.search(workspace_id, "lear").passages  # still typing


def test_phrase_requires_words_together(
    session: Session, workspace_id: str, search: KeywordSearchService
) -> None:
    add_document(session, workspace_id, "a.pdf", ["learning rate schedules"])
    add_document(session, workspace_id, "b.pdf", ["the rate of learning"])

    results = search.search(workspace_id, '"learning rate"')

    assert [passage.file_name for passage in results.passages] == ["a.pdf"]


def test_more_relevant_pages_rank_first(
    session: Session, workspace_id: str, search: KeywordSearchService
) -> None:
    add_document(session, workspace_id, "mentions.pdf", ["A long page " * 50 + "about attention once."])
    add_document(session, workspace_id, "focus.pdf", ["Attention attention: attention is all you need."])

    results = search.search(workspace_id, "attention")

    assert results.passages[0].file_name == "focus.pdf"


def test_search_is_isolated_per_workspace(
    session: Session, workspace_id: str, search: KeywordSearchService
) -> None:
    other = WorkspaceService(session).create_workspace(WorkspaceCreateDTO(name="Other"))
    add_document(session, other.id, "other.pdf", ["transformer architecture"])

    assert search.search(workspace_id, "transformer").is_empty
    assert search.search(other.id, "transformer").passages


def test_finds_documents_by_name(
    session: Session, workspace_id: str, search: KeywordSearchService
) -> None:
    add_document(session, workspace_id, "100%_Exam_Prep.pdf", ["Nothing relevant"])
    add_document(session, workspace_id, "Other.pdf", ["Nothing relevant"])

    assert [m.file_name for m in search.search(workspace_id, "exam").name_matches] == [
        "100%_Exam_Prep.pdf"
    ]
    # % and _ are literal characters, not wildcards.
    assert [m.file_name for m in search.search(workspace_id, "%_").name_matches] == [
        "100%_Exam_Prep.pdf"
    ]


def test_removed_document_leaves_the_index(
    session: Session, workspace_id: str, search: KeywordSearchService
) -> None:
    document = add_document(session, workspace_id, "temp.pdf", ["ephemeral content"])

    DocumentService(session).remove_document(document.id)

    assert search.search(workspace_id, "ephemeral").is_empty
    remaining = session.execute(text("SELECT count(*) FROM page_search")).scalar_one()
    assert remaining == 0


def test_deleting_workspace_clears_its_index(session: Session, search: KeywordSearchService) -> None:
    workspace = WorkspaceService(session).create_workspace(WorkspaceCreateDTO(name="Gone"))
    add_document(session, workspace.id, "gone.pdf", ["content to forget"])

    WorkspaceService(session).delete_workspace(workspace.id)

    remaining = session.execute(text("SELECT count(*) FROM page_search")).scalar_one()
    assert remaining == 0


def test_reindexing_does_not_duplicate(
    session: Session, workspace_id: str, search: KeywordSearchService
) -> None:
    document = add_document(session, workspace_id, "twice.pdf", ["repeated words"])

    search.index_document(document.id)
    search.index_document(document.id)
    session.commit()

    assert len(search.search(workspace_id, "repeated").passages) == 1


def test_unsafe_input_never_errors(
    session: Session, workspace_id: str, search: KeywordSearchService
) -> None:
    add_document(session, workspace_id, "a.pdf", ["some text"])

    for typed in ['"', "*", "NEAR(", "a OR", "-x", "^start", "col:value", "(((", "'; DROP TABLE"]:
        search.search(workspace_id, typed)
