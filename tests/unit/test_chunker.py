from pia.rag.chunker import Chunk, chunk_markdown


def test_chunk_keeps_headings_with_body():
    text = "# Title\n\nIntro.\n\n## Section A\n\nBody A.\n\n## Section B\n\nBody B." * 1
    # max_tokens=4 forces a split between Body A and Body B so each section's
    # heading appears on its own chunk.  Section A must NOT appear in any
    # chunk's text (headings are breadcrumb-only after the fix).
    chunks = chunk_markdown(text, max_tokens=4, overlap_tokens=2)
    assert all(isinstance(c, Chunk) for c in chunks)
    assert any("Section A" in c.headings for c in chunks)
    assert any("Section B" in c.headings for c in chunks)
    # Heading lines must not bleed into body text.
    assert not any("## Section A" in c.text for c in chunks)
    assert not any("## Section B" in c.text for c in chunks)


def test_chunk_overlap_preserved():
    from itertools import pairwise

    text = "para1.\n\npara2.\n\npara3.\n\npara4.\n\npara5.\n\npara6."
    chunks = chunk_markdown(text, max_tokens=10, overlap_tokens=3)
    # Adjacent chunks share at least one token
    for a, b in pairwise(chunks):
        assert set(a.text.split()) & set(b.text.split())


def test_chunk_prepends_leaf_heading_into_body():
    """BM25 recall depends on entity names appearing in the chunk text. When
    the only mention of an entity is in the heading, the leaf heading must be
    prepended into the body text — without the markdown ``##`` prefix, since
    the breadcrumb already carries the structural info."""
    text = "## Halyk Bank deposit rates\n\nKZT 12-month rate is competitive."
    chunks = chunk_markdown(text, max_tokens=200, overlap_tokens=20)
    assert len(chunks) == 1
    chunk = chunks[0]
    assert "Halyk Bank deposit rates" in chunk.text
    # Markdown heading prefix must NOT appear in the body.
    assert "## Halyk Bank deposit rates" not in chunk.text
    # Breadcrumb is preserved.
    assert chunk.headings == ("Halyk Bank deposit rates",)
