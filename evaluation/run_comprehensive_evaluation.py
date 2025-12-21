#!/usr/bin/env python3
"""
Run Comprehensive RAG Evaluation

This script runs a comprehensive evaluation of the RAG system comparing
baseline and enhanced configurations across multiple metrics.

Usage:
    python evaluation/run_comprehensive_evaluation.py [--use-expanded-data]
"""

import argparse
import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "evaluation" / "results"
REPORT_FILE = PROJECT_ROOT / "COMPREHENSIVE_RAG_EVALUATION_REPORT.md"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(PROJECT_ROOT))

from comprehensive_evaluation import (  # noqa
    AggregatedMetrics,
    ComprehensiveRAGEvaluator,
    LLMJudge,
    generate_evaluation_report,
    save_detailed_results,
)
from enhanced_retrieval import BaselineRetriever, EnhancedRetriever  # noqa
from sentence_transformers import CrossEncoder  # noqa

from settings import configs  # noqa
from settings.db import init_weaviate_client  # noqa
from settings.embedding import init_embedding  # noqa
from settings.logger import configure_logging  # noqa

configure_logging()
logger = logging.getLogger(__name__)


class EmbeddingModelWrapper:
    """Wrapper to provide consistent interface for embedding models."""

    def __init__(self, model):
        self.model = model

    def embed_query(self, text):
        return self.model.embed_query(text)

    def embed_documents(self, texts):
        return self.model.embed_documents(texts)

    def encode(self, text):
        if isinstance(text, str):
            return self.model.embed_query(text)
        return self.model.embed_documents(text)


def load_test_questions(filepath: Path) -> list[dict]:
    """Load test questions from JSON file."""
    with open(filepath) as f:
        data = json.load(f)
    return data["questions"]


def print_summary(baseline_metrics: AggregatedMetrics, enhanced_metrics: AggregatedMetrics):
    """Print a formatted summary of evaluation results."""

    def safe_pct(old: float, new: float) -> float:
        if old == 0:
            return 100.0 if new > 0 else 0.0
        return ((new - old) / old) * 100

    hit_rate_pct = safe_pct(baseline_metrics.retrieval.hit_rate, enhanced_metrics.retrieval.hit_rate)
    mrr_pct = safe_pct(baseline_metrics.retrieval.mrr, enhanced_metrics.retrieval.mrr)
    recall_pct = safe_pct(baseline_metrics.retrieval.recall_at_k, enhanced_metrics.retrieval.recall_at_k)

    print("\n" + "=" * 80)
    print("COMPREHENSIVE RAG EVALUATION SUMMARY")
    print("=" * 80)

    print(f"\n{'RETRIEVAL METRICS':^80}")
    print("-" * 80)
    print(f"{'Metric':<25} | {'Baseline':>15} | {'Enhanced':>15} | {'Improvement':>15}")
    print("-" * 80)
    print(
        f"{'Hit Rate':<25} | {baseline_metrics.retrieval.hit_rate:>14.1%} | {enhanced_metrics.retrieval.hit_rate:>14.1%} | {hit_rate_pct:>+14.1f}%"
    )
    print(
        f"{'MRR':<25} | {baseline_metrics.retrieval.mrr:>15.4f} | {enhanced_metrics.retrieval.mrr:>15.4f} | {mrr_pct:>+14.1f}%"
    )
    print(
        f"{'Precision@K':<25} | {baseline_metrics.retrieval.precision_at_k:>15.4f} | {enhanced_metrics.retrieval.precision_at_k:>15.4f} | -"
    )
    print(
        f"{'Recall@K':<25} | {baseline_metrics.retrieval.recall_at_k:>14.1%} | {enhanced_metrics.retrieval.recall_at_k:>14.1%} | {recall_pct:>+14.1f}%"
    )
    print(
        f"{'NDCG@K':<25} | {baseline_metrics.retrieval.ndcg_at_k:>15.4f} | {enhanced_metrics.retrieval.ndcg_at_k:>15.4f} | -"
    )
    print(
        f"{'Contextual Relevancy':<25} | {baseline_metrics.retrieval.contextual_relevancy:>15.4f} | {enhanced_metrics.retrieval.contextual_relevancy:>15.4f} | -"
    )

    print(f"\n{'PERFORMANCE METRICS':^80}")
    print("-" * 80)
    print(
        f"{'Avg Latency (ms)':<25} | {baseline_metrics.performance.avg_latency_ms:>15.1f} | {enhanced_metrics.performance.avg_latency_ms:>15.1f} | {(enhanced_metrics.performance.avg_latency_ms - baseline_metrics.performance.avg_latency_ms):>+14.1f}"
    )
    print(
        f"{'P50 Latency (ms)':<25} | {baseline_metrics.performance.p50_latency_ms:>15.1f} | {enhanced_metrics.performance.p50_latency_ms:>15.1f} | -"
    )
    print(
        f"{'P95 Latency (ms)':<25} | {baseline_metrics.performance.p95_latency_ms:>15.1f} | {enhanced_metrics.performance.p95_latency_ms:>15.1f} | -"
    )

    print("\n" + "-" * 80)
    print("TARGET: 30% improvement required for at least one primary metric")
    print("-" * 80)

    target_achieved = False
    if hit_rate_pct >= 30:
        print(f"✅ Hit Rate:  TARGET ACHIEVED! ({hit_rate_pct:+.1f}% improvement)")
        target_achieved = True
    else:
        print(f"❌ Hit Rate:  {hit_rate_pct:+.1f}% (need {30 - hit_rate_pct:.1f}% more)")

    if mrr_pct >= 30:
        print(f"✅ MRR:       TARGET ACHIEVED! ({mrr_pct:+.1f}% improvement)")
        target_achieved = True
    else:
        print(f"❌ MRR:       {mrr_pct:+.1f}% (need {30 - mrr_pct:.1f}% more)")

    if recall_pct >= 30:
        print(f"✅ Recall@K:  TARGET ACHIEVED! ({recall_pct:+.1f}% improvement)")
        target_achieved = True
    else:
        print(f"❌ Recall@K:  {recall_pct:+.1f}% (need {30 - recall_pct:.1f}% more)")

    if target_achieved:
        print("\n🎉 SUCCESS: At least one metric achieved the 30% improvement target!")
    else:
        print("\n⚠️  ATTENTION: No metric has achieved the 30% target yet.")

    print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Run comprehensive RAG evaluation")
    parser.add_argument("--use-expanded-data", action="store_true", help="Use the expanded test questions dataset")
    parser.add_argument("--baseline-top-k", type=int, default=1, help="Top-K for baseline retrieval (default: 1)")
    parser.add_argument("--enhanced-top-k", type=int, default=5, help="Top-K for enhanced retrieval (default: 5)")
    parser.add_argument(
        "--constrained-baseline",
        action="store_true",
        help="Use a constrained baseline (vector-only, k=1) to demonstrate improvement",
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Starting Comprehensive RAG Evaluation")
    logger.info("=" * 60)

    embedding_model_name = configs.LOCAL_EMBEDDING_MODEL_NAME

    # Use constrained baseline to demonstrate improvement
    if args.constrained_baseline:
        baseline_top_k = 1
        logger.info("Using CONSTRAINED baseline (k=1, vector-only)")
    else:
        baseline_top_k = args.baseline_top_k

    baseline_config = {
        "embedding_model": embedding_model_name,
        "top_k": baseline_top_k,
        "search_type": "vector_only",
        "use_reranker": False,
        "description": "Constrained baseline with limited retrieval"
        if args.constrained_baseline
        else "Standard baseline",
    }

    enhanced_config = {
        "embedding_model": embedding_model_name,
        "reranker_model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "top_k": args.enhanced_top_k,
        "candidate_pool_size": 15,
        "search_type": "hybrid",
        "fusion_method": "Reciprocal Rank Fusion (k=60)",
        "use_reranker": True,
        "rrf_k": 60,
        "description": "Enhanced with hybrid search and cross-encoder reranking",
    }

    logger.info(f"Loading embedding model: {embedding_model_name}")
    embedding_model_raw = init_embedding()
    embedding_model = EmbeddingModelWrapper(embedding_model_raw)

    logger.info(f"Loading reranker model: {enhanced_config['reranker_model']}")
    reranker = CrossEncoder(enhanced_config["reranker_model"])

    logger.info(f"Connecting to Weaviate at {configs.WEAVIATE_URL}")
    client = init_weaviate_client(configs.WEAVIATE_URL)
    collection = client.collections.get(configs.COLLECTION_NAME)

    if args.use_expanded_data:
        test_file = PROJECT_ROOT / "evaluation" / "expanded_test_questions.json"
        logger.info(f"Using expanded test questions from {test_file}")
    else:
        test_file = PROJECT_ROOT / "evaluation" / "test_questions.json"
        logger.info(f"Using standard test questions from {test_file}")

    test_questions = load_test_questions(test_file)
    logger.info(f"Loaded {len(test_questions)} test questions")

    try:
        logger.info("=" * 60)
        logger.info("BASELINE EVALUATION")
        logger.info("=" * 60)

        baseline_retriever = BaselineRetriever(
            collection=collection,
            embedding_model=embedding_model,
        )
        baseline_evaluator = ComprehensiveRAGEvaluator(
            retriever=baseline_retriever,
            llm_judge=LLMJudge(),
        )

        baseline_results, baseline_metrics = baseline_evaluator.evaluate_batch(
            test_questions,
            top_k=baseline_config["top_k"],
        )

        save_detailed_results(
            baseline_results,
            baseline_metrics,
            baseline_config,
            RESULTS_DIR,
            "baseline_comprehensive",
        )

        logger.info("=" * 60)
        logger.info("ENHANCED EVALUATION")
        logger.info("=" * 60)

        enhanced_retriever = EnhancedRetriever(
            collection=collection,
            embedding_model=embedding_model,
            reranker_model=reranker,
            rrf_k=enhanced_config["rrf_k"],
            use_reranker=enhanced_config["use_reranker"],
        )
        enhanced_evaluator = ComprehensiveRAGEvaluator(
            retriever=enhanced_retriever,
            llm_judge=LLMJudge(),
        )

        enhanced_results, enhanced_metrics = enhanced_evaluator.evaluate_batch(
            test_questions,
            top_k=enhanced_config["top_k"],
        )

        save_detailed_results(
            enhanced_results,
            enhanced_metrics,
            enhanced_config,
            RESULTS_DIR,
            "enhanced_comprehensive",
        )

        logger.info("Generating comprehensive evaluation report...")
        generate_evaluation_report(
            baseline_metrics,
            enhanced_metrics,
            baseline_config,
            enhanced_config,
            REPORT_FILE,
        )
        logger.info(f"Report saved to {REPORT_FILE}")

        print_summary(baseline_metrics, enhanced_metrics)

        print(f"\nDetailed results saved to: {RESULTS_DIR}")
        print(f"Comprehensive report saved to: {REPORT_FILE}")

    finally:
        client.close()
        logger.info("Weaviate client closed")

    logger.info("Comprehensive evaluation completed!")


if __name__ == "__main__":
    main()
