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


def test_meaning_finds_passages_without_shared_words(session: Session, workspace_id: str) -> None:
    add_document(session, workspace_id, "adam.pdf", ["Adam keeps moving averages of gradients."])
    add_document(session, workspace_id, "cnn.pdf", ["Convolutional networks for images."])
    embedder = FakeEmbedder()
    embed_all(session, embedder)

    keyword_only = HybridSearchService(session, None).search(workspace_id, "which optimiser works")
    assert keyword_only.passages == []

    results = HybridSearchService(session, embedder).search(workspace_id, "which optimiser works")

    assert results.used_meaning
    assert results.passages[0].file_name == "adam.pdf"
    assert results.passages[0].matched_by == "meaning"


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
