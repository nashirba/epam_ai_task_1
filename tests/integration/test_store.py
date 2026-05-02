import pytest

from pia.embeddings.local import LocalEmbeddings
from pia.rag.chunker import Chunk
from pia.rag.loaders import Document
from pia.rag.store import WeaviateStore


@pytest.mark.integration
def test_store_index_and_retrieve():
    embeddings = LocalEmbeddings()
    store = WeaviateStore(embeddings=embeddings, collection="TestKB", reset=True)
    docs = [
        Document(
            source="news",
            source_url="u1",
            text="NBK raised the base rate to 16.5%",
            metadata={},
            published_at="2026-04-18",
            language="en",
        ),
        Document(
            source="news",
            source_url="u2",
            text="Halyk Bank dividend announcement",
            metadata={},
            published_at="2026-04-20",
            language="en",
        ),
        Document(
            source="user_note",
            source_url="u3",
            text="My target allocation is 30% USD ETFs",
            metadata={},
            published_at="2026-05-01",
            language="en",
        ),
    ]
    chunks = [(d, Chunk(d.text, headings=())) for d in docs]
    store.upsert(chunks)
    hits = store.hybrid_search("base rate", k=3)
    assert hits[0].source == "news"
    assert "rate" in hits[0].text.lower()
    store.close()
