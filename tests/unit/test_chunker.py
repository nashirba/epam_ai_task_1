from pia.rag.chunker import Chunk, chunk_markdown


def test_chunk_keeps_headings_with_body():
    text = "# Title\n\nIntro.\n\n## Section A\n\nBody A.\n\n## Section B\n\nBody B." * 1
    chunks = chunk_markdown(text, max_tokens=20, overlap_tokens=4)
    assert all(isinstance(c, Chunk) for c in chunks)
    assert any("Section A" in c.text for c in chunks)
    assert any("Section B" in c.text for c in chunks)


def test_chunk_overlap_preserved():
    from itertools import pairwise

    text = "para1.\n\npara2.\n\npara3.\n\npara4.\n\npara5.\n\npara6."
    chunks = chunk_markdown(text, max_tokens=10, overlap_tokens=3)
    # Adjacent chunks share at least one token
    for a, b in pairwise(chunks):
        assert set(a.text.split()) & set(b.text.split())
