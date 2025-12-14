import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from enhanced_retrieval import EnhancedRetriever
from sentence_transformers import CrossEncoder, SentenceTransformer

from settings import configs
from settings.db import init_weaviate_client
from settings.logger import configure_logging

PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "evaluation" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

configure_logging()
logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    query_id: str
    query: str
    retrieved_doc_ids: list[str]
    ground_truth_doc_ids: list[str]
    scores: list[dict]
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


def load_test_questions(filepath: Path) -> list[dict]:
    """Load test questions from JSON file."""
    with open(filepath) as f:
        data = json.load(f)
    return data["questions"]


def load_baseline_results(filepath: Path) -> dict:
    """Load baseline results for comparison."""
    if not filepath.exists():
        return None
    with open(filepath) as f:
        return json.load(f)


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
    retriever: EnhancedRetriever, test_questions: list[dict], top_k: int = 5, use_hybrid: bool = True
) -> tuple[list[RetrievalResult], EvaluationMetrics]:
    """Run evaluation on all test questions."""
    results = []

    for q in test_questions:
        query_id = q["id"]
        query = q["question"]
        ground_truth = q["ground_truth_doc_ids"]

        logger.info(f"Evaluating {query_id}: {query[:50]}...")

        try:
            start_time = time.perf_counter()
            docs = retriever.search(query, top_k=top_k, use_hybrid=use_hybrid)
            latency = (time.perf_counter() - start_time) * 1000

            retrieved_ids = [d.doc_id for d in docs]
            scores = [
                {
                    "doc_id": d.doc_id,
                    "vector_score": d.vector_score,
                    "bm25_score": d.bm25_score,
                    "fusion_score": d.fusion_score,
                    "rerank_score": d.rerank_score,
                    "final_rank": d.final_rank,
                }
                for d in docs
            ]

            hit = calculate_hit(retrieved_ids, ground_truth)
            rr = calculate_reciprocal_rank(retrieved_ids, ground_truth)
            p_at_k = calculate_precision_at_k(retrieved_ids, ground_truth)

            result = RetrievalResult(
                query_id=query_id,
                query=query,
                retrieved_doc_ids=retrieved_ids,
                ground_truth_doc_ids=ground_truth,
                scores=scores,
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
    prefix: str = "enhanced",
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
                "scores": r.scores,
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


def print_summary(metrics: EvaluationMetrics, config: dict, baseline_metrics: dict = None):
    """Print evaluation summary with comparison."""
    print("\n" + "=" * 70)
    print("ENHANCED EVALUATION RESULTS")
    print("=" * 70)
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

    if baseline_metrics:
        print("\n" + "-" * 70)
        print("COMPARISON WITH BASELINE")
        print("-" * 70)

        baseline_hr = baseline_metrics["metrics"]["hit_rate_percent"]
        baseline_mrr = baseline_metrics["metrics"]["mrr"]
        baseline_latency = baseline_metrics["metrics"]["avg_latency_ms"]

        hr_change = metrics.hit_rate - baseline_hr
        hr_pct_change = (hr_change / baseline_hr * 100) if baseline_hr > 0 else float("inf")

        mrr_change = metrics.mrr - baseline_mrr
        mrr_pct_change = (mrr_change / baseline_mrr * 100) if baseline_mrr > 0 else float("inf")

        latency_change = metrics.avg_latency_ms - baseline_latency

        print("\n  Metric               | Baseline    | Enhanced    | Change")
        print("  ---------------------|-------------|-------------|---------------")
        print(
            f"  Hit Rate             | {baseline_hr:>9.1f}%  | {metrics.hit_rate:>9.1f}%  | {hr_change:+.1f}% ({hr_pct_change:+.1f}% rel)"
        )
        print(
            f"  MRR                  | {baseline_mrr:>11.4f} | {metrics.mrr:>11.4f} | {mrr_change:+.4f} ({mrr_pct_change:+.1f}% rel)"
        )
        print(
            f"  Latency (ms)         | {baseline_latency:>9.1f}   | {metrics.avg_latency_ms:>9.1f}   | {latency_change:+.1f}ms"
        )

        print("\n" + "-" * 70)
        print("TARGET ACHIEVEMENT")
        print("-" * 70)

        target = 30.0
        if hr_pct_change >= target:
            print(f"  ✅ Hit Rate improvement: {hr_pct_change:.1f}% (TARGET: {target}% - ACHIEVED!)")
        else:
            print(f"  ❌ Hit Rate improvement: {hr_pct_change:.1f}% (TARGET: {target}% - NOT YET)")

        if mrr_pct_change >= target:
            print(f"  ✅ MRR improvement: {mrr_pct_change:.1f}% (TARGET: {target}% - ACHIEVED!)")
        else:
            print(f"  ❌ MRR improvement: {mrr_pct_change:.1f}% (TARGET: {target}% - NOT YET)")

    print("=" * 70 + "\n")


def main():
    logger.info("Starting RAG Enhanced Evaluation")

    config = {
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "reranker_model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "top_k": 5,
        "candidate_pool_size": 15,
        "collection_name": "DietKnowledge",
        "use_hybrid": True,
        "use_reranker": True,
        "rrf_k": 60,
        "distance_metric": "cosine",
    }

    logger.info(f"Loading embedding model: {config['embedding_model']}")
    embedding_model = SentenceTransformer(config["embedding_model"])

    logger.info(f"Loading reranker model: {config['reranker_model']}")
    reranker = CrossEncoder(config["reranker_model"])

    client = init_weaviate_client(configs.WEAVIATE_URL)
    collection = client.collections.get(config["collection_name"])

    retriever = EnhancedRetriever(
        collection=collection,
        embedding_model=embedding_model,
        reranker_model=reranker,
        rrf_k=config["rrf_k"],
        use_reranker=config["use_reranker"],
    )

    test_file = PROJECT_ROOT / "evaluation" / "test_questions.json"
    test_questions = load_test_questions(test_file)
    logger.info(f"Loaded {len(test_questions)} test questions")

    baseline_file = RESULTS_DIR / "baseline_latest.json"
    baseline_results = load_baseline_results(baseline_file)
    if baseline_results:
        logger.info("Loaded baseline results for comparison")
    else:
        logger.warning("No baseline results found - run evaluate_baseline.py first")

    try:
        results, metrics = evaluate_retrieval(
            retriever, test_questions, top_k=config["top_k"], use_hybrid=config["use_hybrid"]
        )
        save_results(results, metrics, config, RESULTS_DIR, prefix="enhanced")
        print_summary(metrics, config, baseline_results)
    finally:
        client.close()
        logger.info("Weaviate client closed")


if __name__ == "__main__":
    main()
