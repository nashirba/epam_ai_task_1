from __future__ import annotations

import uuid
from dataclasses import dataclass

import weaviate
from weaviate.classes.config import Configure, DataType, Property
from weaviate.classes.query import Filter, HybridFusion, MetadataQuery

from pia.config import get_settings
from pia.embeddings.base import EmbeddingProvider
from pia.rag.chunker import Chunk
from pia.rag.loaders import Document


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    source: str
    source_url: str
    published_at: str | None
    language: str | None
    score: float
    headings: tuple[str, ...]


class WeaviateStore:
    def __init__(
        self, *, embeddings: EmbeddingProvider, collection: str = "KB", reset: bool = False
    ) -> None:
        s = get_settings()
        self._client = weaviate.connect_to_local(
            host=s.weaviate_host, port=s.weaviate_http_port, grpc_port=s.weaviate_grpc_port
        )
        self._embeddings = embeddings
        self._collection_name = collection
        if reset and self._client.collections.exists(collection):
            self._client.collections.delete(collection)
        if not self._client.collections.exists(collection):
            self._client.collections.create(
                name=collection,
                vectorizer_config=Configure.Vectorizer.none(),
                properties=[
                    Property(name="content", data_type=DataType.TEXT),
                    Property(name="source", data_type=DataType.TEXT),
                    Property(name="source_url", data_type=DataType.TEXT),
                    Property(name="published_at", data_type=DataType.TEXT),
                    Property(name="language", data_type=DataType.TEXT),
                    Property(name="headings", data_type=DataType.TEXT_ARRAY),
                    Property(name="embedding_model", data_type=DataType.TEXT),
                ],
            )
        self._coll = self._client.collections.get(collection)

    def upsert(self, items: list[tuple[Document, Chunk]]) -> None:
        texts = [c.text for _, c in items]
        vectors = self._embeddings.embed_batch(texts)
        with self._coll.batch.dynamic() as batch:
            for (doc, chunk), vec in zip(items, vectors, strict=True):
                batch.add_object(
                    uuid=uuid.uuid5(
                        uuid.NAMESPACE_URL,
                        f"{doc.source}|{doc.source_url}|{chunk.text[:64]}",
                    ).hex,
                    properties={
                        "content": chunk.text,
                        "source": doc.source,
                        "source_url": doc.source_url,
                        "published_at": str(doc.published_at) if doc.published_at else "",
                        "language": doc.language or "",
                        "headings": list(chunk.headings),
                        "embedding_model": self._embeddings.name,
                    },
                    vector=vec,
                )

    def hybrid_search(
        self,
        query: str,
        *,
        k: int = 5,
        alpha: float = 0.5,
        filter_source: str | None = None,
    ) -> list[RetrievedChunk]:
        flt = Filter.by_property("source").equal(filter_source) if filter_source else None
        qvec = self._embeddings.embed_one(query)
        res = self._coll.query.hybrid(
            query=query,
            vector=qvec,
            alpha=alpha,
            limit=k,
            filters=flt,
            fusion_type=HybridFusion.RELATIVE_SCORE,
            return_metadata=MetadataQuery(score=True),
        )
        out = []
        for o in res.objects:
            p = o.properties
            out.append(
                RetrievedChunk(
                    text=p["content"],
                    source=p["source"],
                    source_url=p["source_url"],
                    published_at=p.get("published_at") or None,
                    language=p.get("language") or None,
                    score=float(o.metadata.score or 0.0),
                    headings=tuple(p.get("headings") or ()),
                )
            )
        return out

    def close(self) -> None:
        self._client.close()
