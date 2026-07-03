from brain.ingest import chunk_text


def test_short_body_is_single_chunk(sandbox):
    assert chunk_text("One short paragraph.") == ["One short paragraph."]


def test_long_body_splits_with_overlap(sandbox):
    paragraphs = [f"Paragraph {i}. " + ("content " * 60) for i in range(6)]
    chunks = chunk_text("\n\n".join(paragraphs))
    assert len(chunks) > 1
    from brain.config import load_config

    max_chars = load_config()["chunking"]["max_chars"]
    overlap = load_config()["chunking"]["overlap_chars"]
    assert all(len(c) <= max_chars + overlap + 2 for c in chunks)
    tail = chunks[0][-overlap:]
    assert tail.split("\n\n")[0] in chunks[1]
