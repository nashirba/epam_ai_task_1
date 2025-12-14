import logging
from dataclasses import dataclass
from typing import Any

import weaviate
from sentence_transformers import CrossEncoder
from weaviate.classes.query import MetadataQuery

logger = logging.getLogger(__name__)


@dataclass
class RetrievedDocument:
    doc_id: str
    title: str
    category: str
    content: str
    vector_score: float | None = None
    bm25_score: float | None = None
    fusion_score: float | None = None
    rerank_score: float | None = None
    final_rank: int | None = None


class EnhancedRetriever:
    """Enhanced retriever with hybrid search and re-ranking."""

    def __init__(
        self,
        collection: weaviate.collections.Collection,
        embedding_model: Any,
        reranker_model: CrossEncoder | None = None,
        rrf_k: int = 60,
        use_reranker: bool = True,
    ):
        self.collection = collection
        self.embedding_model = embedding_model
        self.rrf_k = rrf_k
        self.use_reranker = use_reranker

        if use_reranker:
            if reranker_model is None:
                logger.info("Loading cross-encoder reranker: cross-encoder/ms-marco-MiniLM-L-6-v2")
                self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            else:
                self.reranker = reranker_model
        else:
            self.reranker = None

    def _get_embedding(self, text: str) -> list[float]:
        """Get embedding for text, handling different model interfaces."""
        if hasattr(self.embedding_model, "embed_query"):
            embedding = self.embedding_model.embed_query(text)
        elif hasattr(self.embedding_model, "encode"):
            embedding = self.embedding_model.encode(text)
        else:
            raise ValueError("Embedding model must have 'embed_query' or 'encode' method")

        if hasattr(embedding, "tolist"):
            return embedding.tolist()
        return list(embedding) if not isinstance(embedding, list) else embedding

    def vector_search(self, query: str, limit: int = 10) -> list[RetrievedDocument]:
        """Perform vector similarity search."""
        query_embedding = self._get_embedding(query)

        results = self.collection.query.near_vector(
            near_vector=query_embedding, limit=limit, return_metadata=MetadataQuery(distance=True)
        )

        documents = []
        for obj in results.objects:
            doc = RetrievedDocument(
                doc_id=obj.properties["doc_id"],
                title=obj.properties["title"],
                category=obj.properties["category"],
                content=obj.properties["content"],
                vector_score=1 - obj.metadata.distance if obj.metadata else None,  # Convert distance to similarity
            )
            documents.append(doc)

        return documents

    def bm25_search(self, query: str, limit: int = 10) -> list[RetrievedDocument]:
        """Perform BM25 keyword search."""
        results = self.collection.query.bm25(
            query=query,
            limit=limit,
            return_metadata=MetadataQuery(score=True),
            query_properties=["title", "content", "category"],
        )

        documents = []
        for obj in results.objects:
            doc = RetrievedDocument(
                doc_id=obj.properties["doc_id"],
                title=obj.properties["title"],
                category=obj.properties["category"],
                content=obj.properties["content"],
                bm25_score=obj.metadata.score if obj.metadata else None,
            )
            documents.append(doc)

        return documents

    def reciprocal_rank_fusion(
        self, vector_results: list[RetrievedDocument], bm25_results: list[RetrievedDocument]
    ) -> list[RetrievedDocument]:
        """Combine results using Reciprocal Rank Fusion."""
        doc_map: dict[str, RetrievedDocument] = {}

        for rank, doc in enumerate(vector_results, 1):
            if doc.doc_id not in doc_map:
                doc_map[doc.doc_id] = RetrievedDocument(
                    doc_id=doc.doc_id, title=doc.title, category=doc.category, content=doc.content, fusion_score=0
                )
            doc_map[doc.doc_id].vector_score = doc.vector_score
            doc_map[doc.doc_id].fusion_score = (doc_map[doc.doc_id].fusion_score or 0) + 1 / (self.rrf_k + rank)

        for rank, doc in enumerate(bm25_results, 1):
            if doc.doc_id not in doc_map:
                doc_map[doc.doc_id] = RetrievedDocument(
                    doc_id=doc.doc_id, title=doc.title, category=doc.category, content=doc.content, fusion_score=0
                )
            doc_map[doc.doc_id].bm25_score = doc.bm25_score
            doc_map[doc.doc_id].fusion_score = (doc_map[doc.doc_id].fusion_score or 0) + 1 / (self.rrf_k + rank)

        fused_results = sorted(doc_map.values(), key=lambda x: x.fusion_score or 0, reverse=True)

        return fused_results

    def rerank(self, query: str, documents: list[RetrievedDocument], top_k: int = 5) -> list[RetrievedDocument]:
        """Re-rank documents using cross-encoder."""
        if not self.reranker or not documents:
            return documents[:top_k]

        pairs = [(query, doc.content) for doc in documents]
        scores = self.reranker.predict(pairs)

        for doc, score in zip(documents, scores, strict=True):
            doc.rerank_score = float(score)

        reranked = sorted(documents, key=lambda x: x.rerank_score or 0, reverse=True)

        for i, doc in enumerate(reranked[:top_k], 1):
            doc.final_rank = i

        return reranked[:top_k]

    def search(
        self, query: str, top_k: int = 5, candidate_pool_size: int = 15, use_hybrid: bool = True
    ) -> list[RetrievedDocument]:
        """Perform enhanced search with optional hybrid and reranking."""
        if use_hybrid:
            vector_results = self.vector_search(query, limit=candidate_pool_size)
            bm25_results = self.bm25_search(query, limit=candidate_pool_size)

            logger.debug(f"Vector search returned {len(vector_results)} results")
            logger.debug(f"BM25 search returned {len(bm25_results)} results")

            fused_results = self.reciprocal_rank_fusion(vector_results, bm25_results)
            logger.debug(f"Fusion produced {len(fused_results)} unique results")

            if self.use_reranker:
                final_results = self.rerank(query, fused_results, top_k)
            else:
                final_results = fused_results[:top_k]
                for i, doc in enumerate(final_results, 1):
                    doc.final_rank = i
        else:
            vector_results = self.vector_search(query, limit=candidate_pool_size)

            if self.use_reranker:
                final_results = self.rerank(query, vector_results, top_k)
            else:
                final_results = vector_results[:top_k]
                for i, doc in enumerate(final_results, 1):
                    doc.final_rank = i

        return final_results


class BaselineRetriever:
    """
    Simple baseline retriever for comparison.
    Vector search only, no reranking.
    """

    def __init__(self, collection: weaviate.collections.Collection, embedding_model: Any):
        self.collection = collection
        self.embedding_model = embedding_model

    def _get_embedding(self, text: str) -> list[float]:
        """Get embedding for text, handling different model interfaces."""
        if hasattr(self.embedding_model, "embed_query"):
            embedding = self.embedding_model.embed_query(text)
        elif hasattr(self.embedding_model, "encode"):
            embedding = self.embedding_model.encode(text)
        else:
            raise ValueError("Embedding model must have 'embed_query' or 'encode' method")

        if hasattr(embedding, "tolist"):
            return embedding.tolist()
        return list(embedding) if not isinstance(embedding, list) else embedding

    def search(self, query: str, top_k: int = 5) -> list[RetrievedDocument]:
        """Perform simple vector search."""
        query_embedding = self._get_embedding(query)

        results = self.collection.query.near_vector(
            near_vector=query_embedding, limit=top_k, return_metadata=MetadataQuery(distance=True)
        )

        documents = []
        for i, obj in enumerate(results.objects, 1):
            doc = RetrievedDocument(
                doc_id=obj.properties["doc_id"],
                title=obj.properties["title"],
                category=obj.properties["category"],
                content=obj.properties["content"],
                vector_score=1 - obj.metadata.distance if obj.metadata else None,
                final_rank=i,
            )
            documents.append(doc)

        return documents
