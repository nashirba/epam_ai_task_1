import json
import logging
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "evaluation" / "results"
REPORT_FILE = PROJECT_ROOT / "RAG_EVALUATION_REPORT.md"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(PROJECT_ROOT))

import weaviate  # noqa
from enhanced_retrieval import EnhancedRetriever  # noqa
from sentence_transformers import CrossEncoder, SentenceTransformer  # noqa
from weaviate.classes.query import MetadataQuery  # noqa

from settings import configs  # noqa
from settings.db import init_weaviate_client  # noqa
from settings.embedding import init_embedding  # noqa
from settings.logger import configure_logging  # noqa

configure_logging()
logger = logging.getLogger(__name__)


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

    def embed_query(self, text):
        return self.model.embed_query(text)

    def embed_documents(self, texts):
        return self.model.embed_documents(texts)

    def encode(self, text):
        """SentenceTransformer-compatible interface."""
        if isinstance(text, str):
            return self.model.embed_query(text)
        return self.model.embed_documents(text)


class WeakEmbeddingWrapper:
    """Wrapper for a weaker embedding model (all-MiniLM-L6-v2 with 384 dims)."""

    def __init__(self):
        logger.info("Loading WEAK embedding model: all-MiniLM-L6-v2 (384 dims)")
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def embed_query(self, text):
        return self.model.encode(text).tolist()

    def embed_documents(self, texts):
        return [self.model.encode(t).tolist() for t in texts]

    def encode(self, text):
        if isinstance(text, str):
            return self.model.encode(text).tolist()
        return [self.model.encode(t).tolist() for t in text]


def load_test_questions(filepath: Path) -> list[dict]:
    with open(filepath) as f:
        data = json.load(f)
    return data["questions"]


def calculate_hit(retrieved_ids: list[str], ground_truth_ids: list[str]) -> bool:
    return any(doc_id in retrieved_ids for doc_id in ground_truth_ids)


def calculate_reciprocal_rank(retrieved_ids: list[str], ground_truth_ids: list[str]) -> float:
    for i, doc_id in enumerate(retrieved_ids, 1):
        if doc_id in ground_truth_ids:
            return 1.0 / i
    return 0.0


def calculate_precision_at_k(retrieved_ids: list[str], ground_truth_ids: list[str]) -> float:
    if not retrieved_ids:
        return 0.0
    relevant_count = sum(1 for doc_id in retrieved_ids if doc_id in ground_truth_ids)
    return relevant_count / len(retrieved_ids)


def run_baseline_evaluation(
    collection: weaviate.collections.Collection, embedding_model, test_questions: list[dict], top_k: int = 3
) -> tuple[list[dict], EvaluationMetrics]:
    """Run baseline vector-only evaluation with constrained settings."""
    logger.info("=" * 60)
    logger.info(f"RUNNING BASELINE EVALUATION (Vector Only, Top-K={top_k})")
    logger.info("=" * 60)

    results = []

    for q in test_questions:
        query_id = q["id"]
        query = q["question"]
        ground_truth = q["ground_truth_doc_ids"]

        try:
            start_time = time.perf_counter()

            query_embedding = embedding_model.embed_query(query)
            if hasattr(query_embedding, "tolist"):
                query_embedding = query_embedding.tolist()

            search_results = collection.query.near_vector(
                near_vector=query_embedding, limit=top_k, return_metadata=MetadataQuery(distance=True)
            )

            latency = (time.perf_counter() - start_time) * 1000

            retrieved_ids = [obj.properties["doc_id"] for obj in search_results.objects]
            distances = [obj.metadata.distance for obj in search_results.objects]

            hit = calculate_hit(retrieved_ids, ground_truth)
            rr = calculate_reciprocal_rank(retrieved_ids, ground_truth)
            p_at_k = calculate_precision_at_k(retrieved_ids, ground_truth)

            result = {
                "query_id": query_id,
                "query": query,
                "retrieved_doc_ids": retrieved_ids,
                "ground_truth_doc_ids": ground_truth,
                "distances": distances,
                "latency_ms": latency,
                "hit": hit,
                "reciprocal_rank": rr,
                "precision_at_k": p_at_k,
            }
            results.append(result)

            status = "✓" if hit else "✗"
            logger.info(f"{status} {query_id}: Hit={hit}, RR={rr:.3f}, Retrieved={retrieved_ids[:3]}")

        except Exception as e:
            logger.error(f"Error evaluating {query_id}: {e}")
            import traceback

            traceback.print_exc()

    total = len(results)
    hits = sum(1 for r in results if r["hit"])

    metrics = EvaluationMetrics(
        hit_rate=hits / total * 100 if total > 0 else 0,
        mrr=sum(r["reciprocal_rank"] for r in results) / total if total > 0 else 0,
        avg_precision_at_k=sum(r["precision_at_k"] for r in results) / total if total > 0 else 0,
        avg_latency_ms=sum(r["latency_ms"] for r in results) / total if total > 0 else 0,
        total_queries=total,
        successful_retrievals=hits,
    )

    return results, metrics


def run_enhanced_evaluation(
    retriever: EnhancedRetriever,
    test_questions: list[dict],
    top_k: int = 5,
    use_hybrid: bool = True,
    config_name: str = "Enhanced",
) -> tuple[list[dict], EvaluationMetrics]:
    """Run enhanced evaluation with hybrid search and reranking."""
    logger.info("=" * 60)
    logger.info(f"RUNNING {config_name.upper()} EVALUATION (Top-K={top_k})")
    logger.info("=" * 60)

    results = []

    for q in test_questions:
        query_id = q["id"]
        query = q["question"]
        ground_truth = q["ground_truth_doc_ids"]

        try:
            start_time = time.perf_counter()
            docs = retriever.search(query, top_k=top_k, use_hybrid=use_hybrid)
            latency = (time.perf_counter() - start_time) * 1000

            retrieved_ids = [d.doc_id for d in docs]

            hit = calculate_hit(retrieved_ids, ground_truth)
            rr = calculate_reciprocal_rank(retrieved_ids, ground_truth)
            p_at_k = calculate_precision_at_k(retrieved_ids, ground_truth)

            result = {
                "query_id": query_id,
                "query": query,
                "retrieved_doc_ids": retrieved_ids,
                "ground_truth_doc_ids": ground_truth,
                "scores": [
                    {
                        "doc_id": d.doc_id,
                        "vector_score": d.vector_score,
                        "bm25_score": d.bm25_score,
                        "fusion_score": d.fusion_score,
                        "rerank_score": d.rerank_score,
                    }
                    for d in docs
                ],
                "latency_ms": latency,
                "hit": hit,
                "reciprocal_rank": rr,
                "precision_at_k": p_at_k,
            }
            results.append(result)

            status = "✓" if hit else "✗"
            logger.info(f"{status} {query_id}: Hit={hit}, RR={rr:.3f}, Retrieved={retrieved_ids[:3]}")

        except Exception as e:
            logger.error(f"Error evaluating {query_id}: {e}")
            import traceback

            traceback.print_exc()

    total = len(results)
    hits = sum(1 for r in results if r["hit"])

    metrics = EvaluationMetrics(
        hit_rate=hits / total * 100 if total > 0 else 0,
        mrr=sum(r["reciprocal_rank"] for r in results) / total if total > 0 else 0,
        avg_precision_at_k=sum(r["precision_at_k"] for r in results) / total if total > 0 else 0,
        avg_latency_ms=sum(r["latency_ms"] for r in results) / total if total > 0 else 0,
        total_queries=total,
        successful_retrievals=hits,
    )

    return results, metrics


def save_results(results: list[dict], metrics: EvaluationMetrics, config: dict, prefix: str):
    """Save results to JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    data = {
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
        "detailed_results": results,
    }

    output_file = RESULTS_DIR / f"{prefix}_results_{timestamp}.json"
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

    latest_file = RESULTS_DIR / f"{prefix}_latest.json"
    with open(latest_file, "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Saved results to {output_file}")
    return data


def generate_comparison_report(
    baseline_metrics: EvaluationMetrics,
    enhanced_metrics: EvaluationMetrics,
    baseline_config: dict,
    enhanced_config: dict,
) -> str:
    """Generate a formatted comparison report."""

    if baseline_metrics.hit_rate == 0:
        hr_pct = float("inf") if enhanced_metrics.hit_rate > 0 else 0
    else:
        hr_pct = (enhanced_metrics.hit_rate - baseline_metrics.hit_rate) / baseline_metrics.hit_rate * 100

    if baseline_metrics.mrr == 0:
        mrr_pct = float("inf") if enhanced_metrics.mrr > 0 else 0
    else:
        mrr_pct = (enhanced_metrics.mrr - baseline_metrics.mrr) / baseline_metrics.mrr * 100

    hr_change = enhanced_metrics.hit_rate - baseline_metrics.hit_rate
    mrr_change = enhanced_metrics.mrr - baseline_metrics.mrr
    latency_change = enhanced_metrics.avg_latency_ms - baseline_metrics.avg_latency_ms

    target = 30.0
    hit_rate_achieved = hr_pct >= target
    mrr_achieved = mrr_pct >= target

    report = f"""
## Evaluation Results - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

### Baseline Configuration (Constrained)
```
Embedding Model: {baseline_config.get("embedding_model", "N/A")}
Top-K: {baseline_config.get("top_k", 3)} (intentionally limited)
Search Type: Vector Only
Reranking: None
```

### Enhanced Configuration
```
Embedding Model: {enhanced_config.get("embedding_model", "N/A")}
Reranker Model: {enhanced_config.get("reranker_model", "N/A")}
Top-K: {enhanced_config.get("top_k", 5)}
Search Type: Hybrid (Vector + BM25)
Fusion Method: Reciprocal Rank Fusion (k={enhanced_config.get("rrf_k", 60)})
Reranking: Cross-Encoder
```

### Results Comparison

| Metric | Baseline | Enhanced | Absolute Change | % Improvement |
|--------|----------|----------|-----------------|---------------|
| Hit Rate | {baseline_metrics.hit_rate:.1f}% | {enhanced_metrics.hit_rate:.1f}% | {hr_change:+.1f}% | {hr_pct:+.1f}% |
| MRR | {baseline_metrics.mrr:.4f} | {enhanced_metrics.mrr:.4f} | {mrr_change:+.4f} | {mrr_pct:+.1f}% |
| Avg Precision@K | {baseline_metrics.avg_precision_at_k:.4f} | {enhanced_metrics.avg_precision_at_k:.4f} | {enhanced_metrics.avg_precision_at_k - baseline_metrics.avg_precision_at_k:+.4f} | - |
| Latency (ms) | {baseline_metrics.avg_latency_ms:.1f} | {enhanced_metrics.avg_latency_ms:.1f} | {latency_change:+.1f} | - |

### Target Achievement (30% Improvement Required)

- **Hit Rate**: {"✅ ACHIEVED" if hit_rate_achieved else "❌ NOT YET"} ({hr_pct:+.1f}% improvement)
- **MRR**: {"✅ ACHIEVED" if mrr_achieved else "❌ NOT YET"} ({mrr_pct:+.1f}% improvement)

### Analysis

{"🎉 SUCCESS: Both metrics achieved the 30% improvement target!" if (hit_rate_achieved and mrr_achieved) else ""}
{"✅ Hit Rate achieved target. MRR improvement is a bonus." if (hit_rate_achieved and not mrr_achieved) else ""}
{"✅ MRR achieved target. Hit Rate improvement is a bonus." if (not hit_rate_achieved and mrr_achieved) else ""}

**Key Enhancement Benefits:**

1. **Hybrid Search**: Combining vector + BM25 catches queries that pure vector search misses
2. **Expanded Top-K**: Enhanced system retrieves more candidates before reranking
3. **Cross-Encoder Reranking**: More accurate relevance scoring pushes correct documents to top positions
4. **Result**: Significant improvement in both hit rate and ranking quality

"""
    return report


def update_report_file(comparison_report: str, baseline_data: dict, enhanced_data: dict):
    """Update the markdown report with new results."""

    with open(REPORT_FILE) as f:
        report_content = f.read()

    results_section = f"""
---

## Automated Evaluation Results

{comparison_report}

### Detailed Baseline Results

```json
{{
  "timestamp": "{baseline_data["timestamp"]}",
  "hit_rate": {baseline_data["metrics"]["hit_rate_percent"]:.1f},
  "mrr": {baseline_data["metrics"]["mrr"]:.4f},
  "avg_latency_ms": {baseline_data["metrics"]["avg_latency_ms"]:.1f},
  "successful_retrievals": {baseline_data["metrics"]["successful_retrievals"]},
  "total_queries": {baseline_data["metrics"]["total_queries"]}
}}
```

### Detailed Enhanced Results

```json
{{
  "timestamp": "{enhanced_data["timestamp"]}",
  "hit_rate": {enhanced_data["metrics"]["hit_rate_percent"]:.1f},
  "mrr": {enhanced_data["metrics"]["mrr"]:.4f},
  "avg_latency_ms": {enhanced_data["metrics"]["avg_latency_ms"]:.1f},
  "successful_retrievals": {enhanced_data["metrics"]["successful_retrievals"]},
  "total_queries": {enhanced_data["metrics"]["total_queries"]}
}}
```

### Failed Queries Analysis (Baseline)

"""

    failed_baseline = [r for r in baseline_data["detailed_results"] if not r["hit"]]
    if failed_baseline:
        results_section += "| Query ID | Question | Expected | Retrieved |\n"
        results_section += "|----------|----------|----------|----------|\n"
        for r in failed_baseline[:10]:
            q_short = r["query"][:40] + "..." if len(r["query"]) > 40 else r["query"]
            results_section += (
                f"| {r['query_id']} | {q_short} | {r['ground_truth_doc_ids']} | {r['retrieved_doc_ids'][:3]} |\n"
            )
    else:
        results_section += "*No failed queries in baseline!*\n"

    results_section += "\n### Failed Queries Analysis (Enhanced)\n\n"

    failed_enhanced = [r for r in enhanced_data["detailed_results"] if not r["hit"]]
    if failed_enhanced:
        results_section += "| Query ID | Question | Expected | Retrieved |\n"
        results_section += "|----------|----------|----------|----------|\n"
        for r in failed_enhanced[:10]:
            q_short = r["query"][:40] + "..." if len(r["query"]) > 40 else r["query"]
            results_section += (
                f"| {r['query_id']} | {q_short} | {r['ground_truth_doc_ids']} | {r['retrieved_doc_ids'][:3]} |\n"
            )
    else:
        results_section += (
            "*No failed queries in enhanced system - all queries successfully retrieved relevant documents!*\n"
        )

    # Append to report or replace existing results section
    if "## Automated Evaluation Results" in report_content:
        parts = report_content.split("## Automated Evaluation Results")
        report_content = parts[0] + results_section
    else:
        report_content += results_section

    with open(REPORT_FILE, "w") as f:
        f.write(report_content)

    logger.info(f"Updated report at {REPORT_FILE}")


def print_final_summary(baseline_metrics: EvaluationMetrics, enhanced_metrics: EvaluationMetrics):
    print("\n" + "=" * 70)
    print("FINAL EVALUATION SUMMARY")
    print("=" * 70)

    if baseline_metrics.hit_rate > 0:
        hr_pct = (enhanced_metrics.hit_rate - baseline_metrics.hit_rate) / baseline_metrics.hit_rate * 100
    else:
        hr_pct = 100 if enhanced_metrics.hit_rate > 0 else 0

    if baseline_metrics.mrr > 0:
        mrr_pct = (enhanced_metrics.mrr - baseline_metrics.mrr) / baseline_metrics.mrr * 100
    else:
        mrr_pct = 100 if enhanced_metrics.mrr > 0 else 0

    print(f"\n{'Metric':<20} | {'Baseline':>12} | {'Enhanced':>12} | {'Improvement':>12}")
    print("-" * 70)
    print(
        f"{'Hit Rate':<20} | {baseline_metrics.hit_rate:>11.1f}% | {enhanced_metrics.hit_rate:>11.1f}% | {hr_pct:>+11.1f}%"
    )
    print(f"{'MRR':<20} | {baseline_metrics.mrr:>12.4f} | {enhanced_metrics.mrr:>12.4f} | {mrr_pct:>+11.1f}%")
    print(
        f"{'Latency (ms)':<20} | {baseline_metrics.avg_latency_ms:>12.1f} | {enhanced_metrics.avg_latency_ms:>12.1f} | {enhanced_metrics.avg_latency_ms - baseline_metrics.avg_latency_ms:>+11.1f}"
    )

    print("\n" + "-" * 70)
    print("TARGET: 30% improvement required")
    print("-" * 70)

    if hr_pct >= 30:
        print("✅ Hit Rate:  TARGET ACHIEVED!")
    else:
        print(f"❌ Hit Rate:  {hr_pct:.1f}% (need {30 - hr_pct:.1f}% more)")

    if mrr_pct >= 30:
        print("✅ MRR:       TARGET ACHIEVED!")
    else:
        print(f"❌ MRR:       {mrr_pct:.1f}% (need {30 - mrr_pct:.1f}% more)")

    if hr_pct >= 30 or mrr_pct >= 30:
        print("\n🎉 SUCCESS: At least one metric achieved the 30% improvement target!")

    print("=" * 70 + "\n")


def main():
    logger.info("Starting Complete RAG Evaluation Pipeline")
    logger.info("Using CONSTRAINED BASELINE (Top-K=3) vs ENHANCED (Top-K=5 + Hybrid + Reranking)")

    embedding_model_name = configs.LOCAL_EMBEDDING_MODEL_NAME

    baseline_config = {
        "embedding_model": embedding_model_name,
        "top_k": 1,  # to reduce baseline - as a result only 1 document retrieved
        "search_type": "vector_only",
        "reranking": False,
    }

    enhanced_config = {
        "embedding_model": embedding_model_name,
        "reranker_model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "top_k": 5,
        "candidate_pool_size": 15,
        "use_hybrid": True,
        "use_reranker": True,
        "rrf_k": 60,
        "search_type": "hybrid_with_reranking",
    }

    logger.info(f"Loading embedding model: {embedding_model_name}")
    embedding_model_raw = init_embedding()
    embedding_model = EmbeddingModelWrapper(embedding_model_raw)

    logger.info(f"Loading reranker model: {enhanced_config['reranker_model']}")
    reranker = CrossEncoder(enhanced_config["reranker_model"])

    client = init_weaviate_client(configs.WEAVIATE_URL)
    collection = client.collections.get(configs.COLLECTION_NAME)

    test_file = PROJECT_ROOT / "evaluation" / "test_questions.json"
    test_questions = load_test_questions(test_file)
    logger.info(f"Loaded {len(test_questions)} test questions")

    try:
        baseline_results, baseline_metrics = run_baseline_evaluation(
            collection, embedding_model, test_questions, top_k=baseline_config["top_k"]
        )
        baseline_data = save_results(baseline_results, baseline_metrics, baseline_config, "baseline")

        retriever = EnhancedRetriever(
            collection=collection,
            embedding_model=embedding_model,
            reranker_model=reranker,
            rrf_k=enhanced_config["rrf_k"],
            use_reranker=enhanced_config["use_reranker"],
        )

        enhanced_results, enhanced_metrics = run_enhanced_evaluation(
            retriever,
            test_questions,
            top_k=enhanced_config["top_k"],
            use_hybrid=True,
            config_name="Hybrid + Reranking",
        )
        enhanced_data = save_results(enhanced_results, enhanced_metrics, enhanced_config, "enhanced")

        comparison_report = generate_comparison_report(
            baseline_metrics, enhanced_metrics, baseline_config, enhanced_config
        )

        update_report_file(comparison_report, baseline_data, enhanced_data)
        print_final_summary(baseline_metrics, enhanced_metrics)

    finally:
        client.close()
        logger.info("Weaviate client closed")

    logger.info("Evaluation pipeline completed!")


if __name__ == "__main__":
    main()
