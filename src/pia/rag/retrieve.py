from __future__ import annotations

from pia.embeddings import get_embedding_provider
from pia.rag.store import RetrievedChunk, WeaviateStore


def retrieve(query: str, *, k: int = 5, source: str | None = None) -> list[RetrievedChunk]:
    store = WeaviateStore(embeddings=get_embedding_provider(), collection="KB")
    try:
        return store.hybrid_search(query, k=k, filter_source=source)
    finally:
        store.close()
