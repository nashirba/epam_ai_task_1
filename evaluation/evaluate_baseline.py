import json
import logging
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import weaviate
from weaviate.classes.query import MetadataQuery

PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "evaluation" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(PROJECT_ROOT))

from settings import configs  # noqa
from settings.db import init_weaviate_client  # noqa
from settings.embedding import init_embedding  # noqa
from settings.logger import configure_logging  # noqa

configure_logging()
logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    query_id: str
    query: str
    retrieved_doc_ids: list[str]
    ground_truth_doc_ids: list[str]
    distances: list[float]
    latency_ms: float
    hit: bool
    reciprocal_rank: float
    precision_at_k: float


@dataclass
class EvaluationMetrics:
    hit_rate: float
    mrr: float
    avg_precision_at_k: float
    avg_latency_ms: float
    total_queries: int
    successful_retrievals: int


class EmbeddingModelWrapper:
    """Wrapper to provide consistent interface for embedding models."""

    def __init__(self, model):
        self.model = model

    def encode(self, text):
        if isinstance(text, str):
            return self.model.embed_query(text)
        return self.model.embed_documents(text)


def load_test_questions(filepath: Path) -> list[dict]:
    with open(filepath) as f:
        data = json.load(f)
    return data["questions"]


def search_baseline(
    collection: weaviate.collections.Collection, embedding_model: EmbeddingModelWrapper, query: str, top_k: int = 5
) -> tuple[list[dict], float]:
    """
    Perform baseline vector search (no query expansion for fair comparison).
    Returns retrieved documents and latency in milliseconds.
    """
    start_time = time.perf_counter()

    query_embedding = embedding_model.encode(query)
    if not isinstance(query_embedding, list):
        query_embedding = query_embedding.tolist() if hasattr(query_embedding, "tolist") else list(query_embedding)

    results = collection.query.near_vector(
        near_vector=query_embedding, limit=top_k, return_metadata=MetadataQuery(distance=True)
    )

    latency_ms = (time.perf_counter() - start_time) * 1000

    documents = []
    for obj in results.objects:
        doc = {
            "doc_id": obj.properties["doc_id"],
            "title": obj.properties["title"],
            "category": obj.properties["category"],
            "content": obj.properties["content"],
            "distance": obj.metadata.distance if obj.metadata else None,
        }
        documents.append(doc)

    return documents, latency_ms


def calculate_hit(retrieved_ids: list[str], ground_truth_ids: list[str]) -> bool:
    """Check if any ground truth document is in retrieved results."""
    return any(doc_id in retrieved_ids for doc_id in ground_truth_ids)


def calculate_reciprocal_rank(retrieved_ids: list[str], ground_truth_ids: list[str]) -> float:
    """Calculate reciprocal rank (1/position of first relevant doc)."""
    for i, doc_id in enumerate(retrieved_ids, 1):
        if doc_id in ground_truth_ids:
            return 1.0 / i
    return 0.0


def calculate_precision_at_k(retrieved_ids: list[str], ground_truth_ids: list[str]) -> float:
    """Calculate precision@k (proportion of retrieved docs that are relevant)."""
    if not retrieved_ids:
        return 0.0
    relevant_count = sum(1 for doc_id in retrieved_ids if doc_id in ground_truth_ids)
    return relevant_count / len(retrieved_ids)


def evaluate_retrieval(
    collection: weaviate.collections.Collection,
    embedding_model: EmbeddingModelWrapper,
    test_questions: list[dict],
    top_k: int = 5,
) -> tuple[list[RetrievalResult], EvaluationMetrics]:
    """Run evaluation on all test questions."""
    results = []

    for q in test_questions:
        query_id = q["id"]
        query = q["question"]
        ground_truth = q["ground_truth_doc_ids"]

        logger.info(f"Evaluating {query_id}: {query[:50]}...")

        try:
            docs, latency = search_baseline(collection, embedding_model, query, top_k)
            retrieved_ids = [d["doc_id"] for d in docs]
            distances = [d["distance"] for d in docs]

            hit = calculate_hit(retrieved_ids, ground_truth)
            rr = calculate_reciprocal_rank(retrieved_ids, ground_truth)
            p_at_k = calculate_precision_at_k(retrieved_ids, ground_truth)

            result = RetrievalResult(
                query_id=query_id,
                query=query,
                retrieved_doc_ids=retrieved_ids,
                ground_truth_doc_ids=ground_truth,
                distances=distances,
                latency_ms=latency,
                hit=hit,
                reciprocal_rank=rr,
                precision_at_k=p_at_k,
            )
            results.append(result)

            status = "✓" if hit else "✗"
            logger.info(f"  {status} Hit: {hit}, RR: {rr:.3f}, P@{top_k}: {p_at_k:.3f}, Latency: {latency:.1f}ms")
            logger.info(f"    Retrieved: {retrieved_ids}")
            logger.info(f"    Expected:  {ground_truth}")

        except Exception as e:
            logger.error(f"Error evaluating {query_id}: {e}")
            import traceback

            traceback.print_exc()
            continue

    total = len(results)
    hits = sum(1 for r in results if r.hit)

    metrics = EvaluationMetrics(
        hit_rate=hits / total * 100 if total > 0 else 0,
        mrr=sum(r.reciprocal_rank for r in results) / total if total > 0 else 0,
        avg_precision_at_k=sum(r.precision_at_k for r in results) / total if total > 0 else 0,
        avg_latency_ms=sum(r.latency_ms for r in results) / total if total > 0 else 0,
        total_queries=total,
        successful_retrievals=hits,
    )

    return results, metrics


def save_results(
    results: list[RetrievalResult],
    metrics: EvaluationMetrics,
    config: dict,
    output_dir: Path,
    prefix: str = "baseline",
):
    """Save evaluation results to files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    detailed_results = {
        "timestamp": timestamp,
        "config": config,
        "metrics": {
            "hit_rate_percent": metrics.hit_rate,
            "mrr": metrics.mrr,
            "avg_precision_at_k": metrics.avg_precision_at_k,
            "avg_latency_ms": metrics.avg_latency_ms,
            "total_queries": metrics.total_queries,
            "successful_retrievals": metrics.successful_retrievals,
        },
        "detailed_results": [
            {
                "query_id": r.query_id,
                "query": r.query,
                "retrieved_doc_ids": r.retrieved_doc_ids,
                "ground_truth_doc_ids": r.ground_truth_doc_ids,
                "distances": r.distances,
                "latency_ms": r.latency_ms,
                "hit": r.hit,
                "reciprocal_rank": r.reciprocal_rank,
                "precision_at_k": r.precision_at_k,
            }
            for r in results
        ],
    }

    output_file = output_dir / f"{prefix}_results_{timestamp}.json"
    with open(output_file, "w") as f:
        json.dump(detailed_results, f, indent=2)
    logger.info(f"Saved detailed results to {output_file}")

    latest_file = output_dir / f"{prefix}_latest.json"
    with open(latest_file, "w") as f:
        json.dump(detailed_results, f, indent=2)
    logger.info(f"Saved latest results to {latest_file}")

    return output_file


def print_summary(metrics: EvaluationMetrics, config: dict):
    print("\n" + "=" * 60)
    print("BASELINE EVALUATION RESULTS")
    print("=" * 60)
    print("\nConfiguration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    print("\nMetrics:")
    print(f"  Hit Rate (Precision@K):  {metrics.hit_rate:.1f}%")
    print(f"  Mean Reciprocal Rank:    {metrics.mrr:.4f}")
    print(f"  Avg Context Precision:   {metrics.avg_precision_at_k:.4f}")
    print(f"  Average Latency:         {metrics.avg_latency_ms:.1f}ms")
    print("\nSummary:")
    print(f"  Total Queries:           {metrics.total_queries}")
    print(f"  Successful Retrievals:   {metrics.successful_retrievals}")
    print("=" * 60 + "\n")


def main():
    logger.info("Starting RAG Baseline Evaluation")

    embedding_model_name = configs.LOCAL_EMBEDDING_MODEL_NAME

    config = {
        "embedding_model": embedding_model_name,
        "top_k": 5,
        "collection_name": configs.COLLECTION_NAME,
        "query_expansion": False,  # Disabled for baseline
        "distance_metric": "cosine",
    }

    logger.info(f"Loading embedding model: {embedding_model_name}")
    embedding_model_raw = init_embedding()
    embedding_model = EmbeddingModelWrapper(embedding_model_raw)

    client = init_weaviate_client(configs.WEAVIATE_URL)
    collection = client.collections.get(config["collection_name"])

    test_file = PROJECT_ROOT / "evaluation" / "test_questions.json"
    test_questions = load_test_questions(test_file)
    logger.info(f"Loaded {len(test_questions)} test questions")

    try:
        results, metrics = evaluate_retrieval(collection, embedding_model, test_questions, top_k=config["top_k"])
        save_results(results, metrics, config, RESULTS_DIR, prefix="baseline")
        print_summary(metrics, config)
    finally:
        client.close()
        logger.info("Weaviate client closed")


if __name__ == "__main__":
    main()
