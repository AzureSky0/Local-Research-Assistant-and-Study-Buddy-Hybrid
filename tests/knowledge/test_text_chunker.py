from app.knowledge.services.text_chunker import (
    MAX_WORDS,
    MIN_FINAL_WORDS,
    OVERLAP_WORDS,
    TARGET_WORDS,
    chunk_pages,
)


def sentences(count: int, prefix: str = "Sentence") -> str:
    """Seven-word sentences numbered so they can be found again."""
    return " ".join(f"{prefix} {i} explains gradient descent in detail." for i in range(count))


def test_empty_input_gives_no_chunks() -> None:
    assert chunk_pages([]) == []
    assert chunk_pages([(1, ""), (2, "   \n\n  ")]) == []


def test_short_document_is_one_chunk() -> None:
    chunks = chunk_pages([(1, "A short note about momentum.")])

    assert len(chunks) == 1
    assert chunks[0].text == "A short note about momentum."
    assert (chunks[0].start_page, chunks[0].end_page) == (1, 1)
    assert chunks[0].word_count == 5


def test_chunks_respect_size_limits() -> None:
    chunks = chunk_pages([(page, sentences(60, f"P{page}")) for page in range(1, 6)])

    assert len(chunks) > 1
    assert all(chunk.word_count <= MAX_WORDS for chunk in chunks)
    # All but the last reach the target size.
    assert all(chunk.word_count >= TARGET_WORDS for chunk in chunks[:-1])
    assert [chunk.index for chunk in chunks] == list(range(len(chunks)))


def test_chunks_end_on_sentence_boundaries() -> None:
    chunks = chunk_pages([(1, sentences(100))])

    assert all(chunk.text.endswith("detail.") for chunk in chunks)


def test_neighbouring_chunks_overlap() -> None:
    chunks = chunk_pages([(1, sentences(100))])

    for previous, current in zip(chunks, chunks[1:]):
        first_sentence = current.text.split(".")[0] + "."
        assert first_sentence in previous.text

        overlap = len(first_sentence.split())
        assert 0 < overlap <= OVERLAP_WORDS


def test_page_ranges_are_tracked() -> None:
    chunks = chunk_pages([(1, sentences(20, "First")), (2, sentences(20, "Second")), (3, sentences(20, "Third"))])

    assert chunks[0].start_page == 1
    assert chunks[-1].end_page == 3
    spanning = [chunk for chunk in chunks if chunk.start_page != chunk.end_page]
    assert spanning, "a chunk should span a page break"


def test_markdown_heading_starts_a_new_chunk() -> None:
    text = sentences(40) + "\n\n## Momentum\n\n" + sentences(10, "Momentum")

    chunks = chunk_pages([(1, text)])

    heading_chunks = [chunk for chunk in chunks if "## Momentum" in chunk.text]
    assert len(heading_chunks) == 1
    assert heading_chunks[0].text.startswith("## Momentum")


def test_small_leftover_joins_previous_chunk() -> None:
    # 34 seven-word sentences: a 224-word chunk plus a 14-word remainder,
    # which is too small to stand alone and still fits the maximum.
    chunks = chunk_pages([(1, sentences(34))])

    assert len(chunks) == 1
    assert chunks[0].word_count == 238
    assert 238 - 224 < MIN_FINAL_WORDS


def test_text_without_punctuation_is_split_into_word_runs() -> None:
    chunks = chunk_pages([(1, "data " * 1000)])

    assert len(chunks) >= 4
    assert all(chunk.word_count <= MAX_WORDS for chunk in chunks)
    assert sum(chunk.word_count for chunk in chunks) >= 1000


def test_paragraph_breaks_are_kept_inside_chunks() -> None:
    chunks = chunk_pages([(1, "First paragraph here.\n\nSecond paragraph here.")])

    assert chunks[0].text == "First paragraph here.\n\nSecond paragraph here."


def test_chunking_is_deterministic() -> None:
    pages = [(1, sentences(80)), (2, "# Notes\n\n" + sentences(50))]

    assert chunk_pages(pages) == chunk_pages(pages)
