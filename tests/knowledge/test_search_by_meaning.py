from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.documents.domain import Document, DocumentProcessingStatus
from app.documents.repository.document_page_repository import DocumentPageRepository
from app.documents.services.document_service import DocumentService
from app.knowledge.dto.search_results import HIGHLIGHT_START
from app.knowledge.orm.vector_index_schema import existing_vector_tables, vector_table_name
from app.knowledge.repository.vector_repository import VectorRepository
from app.knowledge.services.chunking_service import ChunkingService
from app.knowledge.services.embedding_service import EmbeddingService
from app.knowledge.services.hybrid_search_service import HybridSearchService, _excerpt
from app.knowledge.services.keyword_search_service import KeywordSearchService
from app.workspace.dto.workspace_create import WorkspaceCreateDTO
from app.workspace.services.workspace_service import WorkspaceService
from tests.knowledge.fake_embedder import FAKE_SPEC, OTHER_FAKE_SPEC, FakeEmbedder


def add_document(session: Session, workspace_id: str, file_name: str, pages: list[str]) -> Document:
    """A processed document: pages, keyword index and chunks."""
    document = DocumentService(session).create_document(
        Document(
            id=str(uuid4()),
            workspace_id=workspace_id,
            file_name=file_name,
            original_path=f"D:/papers/{file_name}",
            file_size=sum(len(p) for p in pages),
            checksum=str(uuid4()),
            file_type="pdf",
            imported_at=datetime.now(UTC),
            processing_status=DocumentProcessingStatus.READY,
        )
    )
    numbered = list(enumerate(pages, start=1))
    DocumentPageRepository(session).add_pages(document.id, numbered)
    KeywordSearchService(session).index_document(document.id)
    ChunkingService(session).chunk_document(document.id, numbered)
    session.commit()
    return document


def embed_all(session: Session, embedder: FakeEmbedder | None = None) -> EmbeddingService:
    service = EmbeddingService(session, embedder or FakeEmbedder())
    service.prepare()
    service.embed_pending()
    return service


# Embedding ---------------------------------------------------------------------------


def test_every_chunk_gets_a_vector(session: Session, workspace_id: str) -> None:
    add_document(session, workspace_id, "a.pdf", ["Adam keeps moving averages of gradients."])
    add_document(session, workspace_id, "b.pdf", ["Convolutional networks.", "Pooling layers."])

    service = embed_all(session)

    done, total = service.progress()
    assert done == total > 0
    stored = session.execute(text(f"SELECT count(*) FROM {vector_table_name(FAKE_SPEC)}")).scalar_one()
    assert stored == total


def test_embedding_resumes_after_interruption(session: Session, workspace_id: str) -> None:
    for i in range(3):
        add_document(session, workspace_id, f"doc{i}.pdf", [f"Document {i} text about topic {i}."])

    service = EmbeddingService(session, FakeEmbedder())
    service.prepare()

    # Cancel immediately: nothing embedded, nothing lost.
    assert service.embed_pending(is_cancelled=lambda: True) == 0
    assert service.progress()[0] == 0

    assert service.embed_pending() == 3
    assert service.progress() == (3, 3)

    # Nothing left to do on a second run.
    assert service.embed_pending() == 0


def test_rechunked_and_deleted_documents_keep_index_consistent(
    session: Session, workspace_id: str
) -> None:
    document = add_document(session, workspace_id, "a.pdf", ["Original text."])
    embed_all(session)
    table = vector_table_name(FAKE_SPEC)

    # Re-chunking replaces chunks: their old vectors are removed by the trigger.
    ChunkingService(session).chunk_document(document.id, [(1, "Rewritten text.")])
    session.commit()
    assert session.execute(text(f"SELECT count(*) FROM {table}")).scalar_one() == 0
    assert EmbeddingService(session, FakeEmbedder()).progress() == (0, 1)

    embed_all(session)
    assert session.execute(text(f"SELECT count(*) FROM {table}")).scalar_one() == 1

    # Deleting the document removes its vectors too.
    DocumentService(session).remove_document(document.id)
    assert session.execute(text(f"SELECT count(*) FROM {table}")).scalar_one() == 0


def test_deleting_a_workspace_removes_its_vectors(session: Session) -> None:
    workspace = WorkspaceService(session).create_workspace(WorkspaceCreateDTO(name="Gone"))
    add_document(session, workspace.id, "a.pdf", ["Some text."])
    embed_all(session)

    WorkspaceService(session).delete_workspace(workspace.id)

    count = session.execute(text(f"SELECT count(*) FROM {vector_table_name(FAKE_SPEC)}")).scalar_one()
    assert count == 0


def test_switching_models_rebuilds_the_index(session: Session, workspace_id: str) -> None:
    add_document(session, workspace_id, "a.pdf", ["Some text.", "More text."])
    embed_all(session)

    other = EmbeddingService(session, FakeEmbedder(OTHER_FAKE_SPEC))
    other.prepare()

    tables = existing_vector_tables(session.connection())
    assert tables == [vector_table_name(OTHER_FAKE_SPEC)]
    assert other.progress()[0] == 0

    other.embed_pending()
    assert other.progress()[0] == other.progress()[1]


def test_nearest_only_searches_one_workspace(session: Session, workspace_id: str) -> None:
    other = WorkspaceService(session).create_workspace(WorkspaceCreateDTO(name="Other"))
    add_document(session, workspace_id, "mine.pdf", ["Adam optimizer details."])
    add_document(session, other.id, "theirs.pdf", ["Adam optimizer details."])
    embedder = FakeEmbedder()
    embed_all(session, embedder)

    matches = VectorRepository(session, FAKE_SPEC).nearest(
        workspace_id, embedder.embed_query("adam"), 10
    )

    assert len(matches) == 1


# Hybrid search -----------------------------------------------------------------------------


def test_meaning_finds_passages_by_paraphrase(session: Session, workspace_id: str) -> None:
    add_document(session, workspace_id, "adam.pdf", ["Adam keeps moving averages of gradients."])
    add_document(session, workspace_id, "cnn.pdf", ["Convolutional networks for images."])
    embedder = FakeEmbedder()
    embed_all(session, embedder)

    # "optimiser" is not in the text; "averages" is, so the document's own
    # words support the search and meaning ranks the right passage.
    results = HybridSearchService(session, embedder).search(workspace_id, "optimiser averages")

    assert results.used_meaning
    assert [p.file_name for p in results.passages] == ["adam.pdf"]
    assert results.passages[0].matched_by == "both"


def test_random_text_finds_nothing(session: Session, workspace_id: str) -> None:
    add_document(session, workspace_id, "adam.pdf", ["Adam keeps moving averages of gradients."])
    add_document(session, workspace_id, "cnn.pdf", ["Convolutional networks for images."])
    embedder = FakeEmbedder()
    embed_all(session, embedder)

    # One stray word ("networks") is not evidence, and nearest neighbours
    # alone are never shown.
    results = HybridSearchService(session, embedder).search(
        workspace_id, "purple bicycle dancing networks tomorrow morning"
    )

    assert results.passages == []
    assert results.is_empty


def test_meaning_alone_is_not_evidence(session: Session, workspace_id: str) -> None:
    add_document(session, workspace_id, "adam.pdf", ["Adam keeps moving averages of gradients."])
    embedder = FakeEmbedder()
    embed_all(session, embedder)

    # The fake model treats "optimiser" as close to "adam", but no word of
    # the search is in the document.
    results = HybridSearchService(session, embedder).search(workspace_id, "which optimiser works")

    assert results.passages == []


def test_pages_with_enough_of_a_long_search_are_kept(session: Session, workspace_id: str) -> None:
    add_document(
        session,
        workspace_id,
        "gan.pdf",
        ["A generator and a discriminator are trained together.", "Images only."],
    )

    results = HybridSearchService(session, None).search(
        workspace_id, "generator discriminator training networks images stability"
    )

    assert [p.page_number for p in results.passages] == [1]
    assert results.total_passages == 1


def test_words_and_meaning_are_combined(session: Session, workspace_id: str) -> None:
    add_document(session, workspace_id, "adam.pdf", ["The Adam optimizer uses moving averages."])
    embedder = FakeEmbedder()
    embed_all(session, embedder)

    results = HybridSearchService(session, embedder).search(workspace_id, "adam optimizer")

    assert results.passages[0].matched_by == "both"
    # The highlighted keyword snippet is kept.
    assert HIGHLIGHT_START in results.passages[0].snippet


def test_without_vectors_search_is_keyword_only(session: Session, workspace_id: str) -> None:
    add_document(session, workspace_id, "adam.pdf", ["Adam optimizer."])

    results = HybridSearchService(session, FakeEmbedder()).search(workspace_id, "adam")

    assert not results.used_meaning
    assert results.passages[0].matched_by == "words"


def test_unavailable_model_falls_back_to_words(session: Session, workspace_id: str) -> None:
    add_document(session, workspace_id, "adam.pdf", ["Adam optimizer."])
    embed_all(session)

    results = HybridSearchService(session, FakeEmbedder(unavailable=True)).search(workspace_id, "adam")

    assert not results.used_meaning
    assert results.passages


def test_meaning_progress_is_reported(session: Session, workspace_id: str) -> None:
    add_document(session, workspace_id, "a.pdf", ["Adam optimizer."])
    service = EmbeddingService(session, FakeEmbedder())
    service.prepare()

    add_document(session, workspace_id, "b.pdf", ["Second document."])
    results = HybridSearchService(session, FakeEmbedder()).search(workspace_id, "adam")
    assert results.meaning_progress == (0, 2)


@pytest.mark.parametrize(
    ("text", "words", "expected_start"),
    [
        ("one two three", ["two"], "one \x02two\x03 three"),
        (" ".join(f"w{i}" for i in range(100)) + " gradient descent", ["gradient"], "…"),
    ],
)
def test_excerpt_centres_on_matching_words(text: str, words: list[str], expected_start: str) -> None:
    excerpt = _excerpt(text, words)
    assert excerpt.startswith(expected_start)
    assert "\x02gradient\x03" in excerpt or words != ["gradient"]


def test_unrelated_passages_are_not_added(session: Session, workspace_id: str) -> None:
    add_document(session, workspace_id, "adam.pdf", ["Adam optimizer."])
    add_document(session, workspace_id, "unrelated.pdf", ["Completely different subject."])
    embedder = FakeEmbedder()
    embed_all(session, embedder)

    results = HybridSearchService(session, embedder).search(workspace_id, "adam")

    assert [p.file_name for p in results.passages] == ["adam.pdf"]


def test_word_match_inside_a_meaning_passage_is_one_result(
    session: Session, workspace_id: str
) -> None:
    # Three short pages form one chunk spanning pages 1-3.
    add_document(session, workspace_id, "book.pdf", ["Contents", "Preface", "Backpropagation explained"])
    embedder = FakeEmbedder()
    embed_all(session, embedder)

    results = HybridSearchService(session, embedder).search(workspace_id, "backpropagation")

    assert len(results.passages) == 1
    assert results.passages[0].page_number == 3
    assert results.passages[0].matched_by == "both"


def test_number_tables_are_not_shown_as_meaning_matches(session: Session, workspace_id: str) -> None:
    add_document(session, workspace_id, "table.pdf", ["optimiser 68.9 12.6 83.0 72.5 48.6 45.4 52.6 55.5 76.0 81.1"])
    add_document(session, workspace_id, "adam.pdf", ["Adam is an optimizer with moving averages."])
    embedder = FakeEmbedder()
    embed_all(session, embedder)

    results = HybridSearchService(session, embedder).search(workspace_id, "which adam works")

    assert [p.file_name for p in results.passages] == ["adam.pdf"]


def test_contents_pages_come_after_real_pages(session: Session, workspace_id: str) -> None:
    contents = (
        "Contents\n"
        "1.1 Maximum Flow . . . . . . . . . . . . 3\n"
        "1.1.3 Shortest Augmenting Path (Edmonds-Karp Algorithm) . . . . . . . . 8\n"
        "1.1.4 Analysis of Edmonds-Karp . . . . . . . . . . 9\n"
        "1.2 Matchings . . . . . . . . . . . . . 12\n"
        "1.3 Minimum Cuts . . . . . . . . . . . . 15\n"
    )
    # A real section page is long; the contents page is short and dense.
    real = (
        "The Edmonds-Karp algorithm always augments along a shortest path, so it runs in polynomial time. "
        + "Each augmentation saturates at least one edge of the residual network and distances never shrink. " * 25
    )
    add_document(session, workspace_id, "notes.pdf", [contents, real])

    results = HybridSearchService(session, None).search(workspace_id, "edmonds karp")

    assert [p.page_number for p in results.passages] == [2, 1]


def test_meaning_only_passages_must_share_a_word_with_the_search(
    session: Session, workspace_id: str
) -> None:
    # Long pages, so each page becomes its own passage.
    page_about_adam = "Adam is an optimizer for training networks. " + "stochastic gradient update rule " * 70
    page_without_the_word = "optimiser settings and optimiser choice " * 80
    add_document(session, workspace_id, "notes.pdf", [page_about_adam, page_without_the_word])
    embedder = FakeEmbedder()
    embed_all(session, embedder)

    results = HybridSearchService(session, embedder).search(workspace_id, "adam")

    # The fake model puts "optimiser" next to "adam", but page 2 never says "adam".
    assert results.used_meaning
    assert all(p.page_number == 1 for p in results.passages)
