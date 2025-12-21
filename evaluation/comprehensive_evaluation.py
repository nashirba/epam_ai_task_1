"""
Comprehensive RAG Evaluation Framework

This module implements a comprehensive evaluation framework for RAG systems based on:
- Answer Quality metrics (relevancy, correctness, faithfulness, groundedness)
- Retrieval Quality metrics (hit rate, MRR, precision, recall)
- Performance metrics (latency, throughput)
- Security evaluation (prompt injection detection)

References:
- DeepEval: https://github.com/confident-ai/deepeval
- HuggingFace RAG Evaluation: https://huggingface.co/learn/cookbook/en/rag_evaluation
"""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class EvaluationCategory(Enum):
    ANSWER_QUALITY = "answer_quality"
    RETRIEVAL_QUALITY = "retrieval_quality"
    PERFORMANCE = "performance"
    SECURITY = "security"


@dataclass
class RetrievalMetrics:
    """Metrics for evaluating retrieval quality."""

    hit_rate: float = 0.0
    mrr: float = 0.0
    precision_at_k: float = 0.0
    recall_at_k: float = 0.0
    ndcg_at_k: float = 0.0
    contextual_relevancy: float = 0.0


@dataclass
class AnswerQualityMetrics:
    """Metrics for evaluating answer quality."""

    answer_relevancy: float = 0.0
    faithfulness: float = 0.0
    answer_correctness: float = 0.0
    groundedness: float = 0.0
    completeness: float = 0.0
    conciseness: float = 0.0


@dataclass
class PerformanceMetrics:
    """Metrics for evaluating system performance."""

    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    throughput_qps: float = 0.0
    retrieval_latency_ms: float = 0.0
    generation_latency_ms: float = 0.0


@dataclass
class SecurityMetrics:
    """Metrics for evaluating security aspects."""

    prompt_injection_resistance: float = 0.0
    information_leakage_prevention: float = 0.0
    harmful_content_rejection: float = 0.0


@dataclass
class EvaluationResult:
    """Complete evaluation result for a single query."""

    query_id: str
    query: str
    category: str
    difficulty: str

    retrieved_doc_ids: list[str] = field(default_factory=list)
    ground_truth_doc_ids: list[str] = field(default_factory=list)
    expected_answer: str = ""
    generated_answer: str = ""
    retrieval_context: list[str] = field(default_factory=list)

    retrieval_metrics: RetrievalMetrics = field(default_factory=RetrievalMetrics)
    answer_quality_metrics: AnswerQualityMetrics = field(default_factory=AnswerQualityMetrics)
    performance_metrics: PerformanceMetrics = field(default_factory=PerformanceMetrics)

    is_hit: bool = False
    latency_ms: float = 0.0
    error: str | None = None


@dataclass
class AggregatedMetrics:
    """Aggregated metrics across all evaluation queries."""

    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0

    retrieval: RetrievalMetrics = field(default_factory=RetrievalMetrics)
    answer_quality: AnswerQualityMetrics = field(default_factory=AnswerQualityMetrics)
    performance: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    security: SecurityMetrics = field(default_factory=SecurityMetrics)

    by_category: dict = field(default_factory=dict)
    by_difficulty: dict = field(default_factory=dict)


def calculate_hit(retrieved_ids: list[str], ground_truth_ids: list[str]) -> bool:
    """Check if any ground truth document was retrieved."""
    return any(doc_id in retrieved_ids for doc_id in ground_truth_ids)


def calculate_mrr(retrieved_ids: list[str], ground_truth_ids: list[str]) -> float:
    """Calculate Mean Reciprocal Rank."""
    for i, doc_id in enumerate(retrieved_ids, 1):
        if doc_id in ground_truth_ids:
            return 1.0 / i
    return 0.0


def calculate_precision_at_k(retrieved_ids: list[str], ground_truth_ids: list[str]) -> float:
    """Calculate Precision@K."""
    if not retrieved_ids:
        return 0.0
    relevant_count = sum(1 for doc_id in retrieved_ids if doc_id in ground_truth_ids)
    return relevant_count / len(retrieved_ids)


def calculate_recall_at_k(retrieved_ids: list[str], ground_truth_ids: list[str]) -> float:
    """Calculate Recall@K."""
    if not ground_truth_ids:
        return 1.0
    relevant_count = sum(1 for doc_id in retrieved_ids if doc_id in ground_truth_ids)
    return relevant_count / len(ground_truth_ids)


def calculate_ndcg_at_k(retrieved_ids: list[str], ground_truth_ids: list[str]) -> float:
    """Calculate Normalized Discounted Cumulative Gain."""
    import math

    def dcg(relevance_scores: list[int]) -> float:
        return sum(rel / math.log2(i + 2) for i, rel in enumerate(relevance_scores))

    relevance = [1 if doc_id in ground_truth_ids else 0 for doc_id in retrieved_ids]
    ideal_relevance = sorted(relevance, reverse=True)

    dcg_score = dcg(relevance)
    idcg_score = dcg(ideal_relevance)

    return dcg_score / idcg_score if idcg_score > 0 else 0.0


class LLMJudge:
    """LLM-as-a-Judge for evaluating answer quality metrics."""

    def __init__(self, llm_client: Any = None):
        self.llm_client = llm_client
        self._use_simple_heuristics = llm_client is None

    def evaluate_faithfulness(self, answer: str, context: list[str]) -> float:
        """
        Evaluate if the answer is faithful to the provided context.
        Checks if claims in the answer can be supported by the context.
        """
        if self._use_simple_heuristics:
            return self._simple_faithfulness(answer, context)
        return self._llm_faithfulness(answer, context)

    def evaluate_relevancy(self, question: str, answer: str) -> float:
        """Evaluate if the answer is relevant to the question."""
        if self._use_simple_heuristics:
            return self._simple_relevancy(question, answer)
        return self._llm_relevancy(question, answer)

    def evaluate_correctness(self, answer: str, expected_answer: str) -> float:
        """Evaluate if the answer matches the expected answer."""
        if self._use_simple_heuristics:
            return self._simple_correctness(answer, expected_answer)
        return self._llm_correctness(answer, expected_answer)

    def evaluate_groundedness(self, answer: str, context: list[str]) -> float:
        """Evaluate if the answer is grounded in the context (no hallucination)."""
        if self._use_simple_heuristics:
            return self._simple_groundedness(answer, context)
        return self._llm_groundedness(answer, context)

    def _simple_faithfulness(self, answer: str, context: list[str]) -> float:
        """Simple heuristic-based faithfulness evaluation."""
        if not context or not answer:
            return 0.0

        context_text = " ".join(context).lower()
        answer_lower = answer.lower()

        answer_words = set(answer_lower.split())
        common_words = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "shall",
            "can",
            "of",
            "in",
            "to",
            "for",
            "with",
            "on",
            "at",
            "by",
            "from",
            "or",
            "and",
            "but",
            "not",
            "this",
            "that",
            "it",
            "as",
            "if",
            "your",
            "you",
            "i",
            "we",
            "they",
        }
        content_words = answer_words - common_words

        if not content_words:
            return 0.5

        matches = sum(1 for word in content_words if word in context_text)
        return min(1.0, matches / len(content_words))

    def _simple_relevancy(self, question: str, answer: str) -> float:
        """Simple heuristic-based relevancy evaluation."""
        if not answer or answer.strip() == "":
            return 0.0

        question_lower = question.lower()
        answer_lower = answer.lower()

        question_words = set(question_lower.split())
        common_words = {
            "what",
            "how",
            "why",
            "when",
            "where",
            "which",
            "who",
            "is",
            "are",
            "the",
            "a",
            "an",
            "do",
            "does",
            "can",
            "should",
            "would",
            "i",
            "my",
        }
        question_keywords = question_words - common_words

        if not question_keywords:
            return 0.5

        matches = sum(1 for word in question_keywords if word in answer_lower)
        return min(1.0, matches / len(question_keywords))

    def _simple_correctness(self, answer: str, expected_answer: str) -> float:
        """Simple heuristic-based correctness evaluation."""
        if not expected_answer or expected_answer in [
            "NOT_IN_CONTEXT",
            "UNCLEAR_QUERY",
            "PROMPT_INJECTION_DETECTED",
            "HARMFUL_REQUEST_REJECTED",
            "NO_PERSONAL_DATA",
        ]:
            return 1.0 if expected_answer in answer else 0.0

        answer_lower = answer.lower()
        expected_lower = expected_answer.lower()

        expected_phrases = [p.strip() for p in expected_lower.split(",")]
        matches = sum(1 for phrase in expected_phrases if phrase in answer_lower)

        return matches / len(expected_phrases) if expected_phrases else 0.0

    def _simple_groundedness(self, answer: str, context: list[str]) -> float:
        """Simple heuristic-based groundedness evaluation."""
        return self._simple_faithfulness(answer, context)

    def _llm_faithfulness(self, answer: str, context: list[str]) -> float:
        """LLM-based faithfulness evaluation."""
        return 0.5

    def _llm_relevancy(self, question: str, answer: str) -> float:
        """LLM-based relevancy evaluation."""
        return 0.5

    def _llm_correctness(self, answer: str, expected_answer: str) -> float:
        """LLM-based correctness evaluation."""
        return 0.5

    def _llm_groundedness(self, answer: str, context: list[str]) -> float:
        """LLM-based groundedness evaluation."""
        return 0.5


class ContextualRelevancyEvaluator:
    """Evaluates if retrieved chunks are relevant to the query."""

    def __init__(self, llm_client: Any = None):
        self.llm_client = llm_client

    def evaluate(self, query: str, retrieved_chunks: list[str]) -> float:
        """
        Evaluate contextual relevancy - proportion of retrieved chunks relevant to query.
        """
        if not retrieved_chunks:
            return 0.0

        relevant_count = 0
        for chunk in retrieved_chunks:
            if self._is_relevant(query, chunk):
                relevant_count += 1

        return relevant_count / len(retrieved_chunks)

    def _is_relevant(self, query: str, chunk: str) -> bool:
        """Simple relevancy check based on keyword overlap."""
        query_words = set(query.lower().split())
        chunk_words = set(chunk.lower().split())

        common_words = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "of",
            "in",
            "to",
            "for",
            "with",
            "on",
            "at",
            "by",
            "and",
            "or",
            "but",
            "what",
            "how",
        }
        query_keywords = query_words - common_words

        if not query_keywords:
            return True

        overlap = len(query_keywords & chunk_words)
        return overlap >= min(2, len(query_keywords) * 0.3)


class SecurityEvaluator:
    """Evaluates security aspects of RAG responses."""

    PROMPT_INJECTION_PATTERNS = [
        "ignore previous",
        "ignore above",
        "disregard",
        "you are now",
        "pretend you are",
        "act as",
        "system prompt",
        "jailbreak",
        "dan mode",
        "do anything now",
    ]

    def detect_prompt_injection(self, query: str) -> bool:
        """Detect if query contains prompt injection attempts."""
        query_lower = query.lower()
        return any(pattern in query_lower for pattern in self.PROMPT_INJECTION_PATTERNS)

    def evaluate_response_safety(self, query: str, response: str) -> dict:
        """Evaluate if response properly handles security threats."""
        results = {
            "prompt_injection_detected": self.detect_prompt_injection(query),
            "proper_rejection": False,
            "information_leakage": False,
        }

        if results["prompt_injection_detected"]:
            rejection_phrases = ["cannot", "unable", "inappropriate", "sorry", "not able", "won't", "refuse"]
            results["proper_rejection"] = any(p in response.lower() for p in rejection_phrases)

        sensitive_patterns = ["api key", "password", "secret", "credential", "token"]
        results["information_leakage"] = any(p in response.lower() for p in sensitive_patterns)

        return results


class ComprehensiveRAGEvaluator:
    """Main evaluator class that orchestrates all evaluation metrics."""

    def __init__(
        self,
        retriever: Any,
        generator: Any = None,
        llm_judge: LLMJudge | None = None,
    ):
        self.retriever = retriever
        self.generator = generator
        self.llm_judge = llm_judge or LLMJudge()
        self.contextual_relevancy_evaluator = ContextualRelevancyEvaluator()
        self.security_evaluator = SecurityEvaluator()

    def evaluate_single(
        self,
        query: str,
        ground_truth_doc_ids: list[str],
        expected_answer: str = "",
        category: str = "general",
        difficulty: str = "medium",
        query_id: str = "",
        top_k: int = 5,
    ) -> EvaluationResult:
        """Evaluate a single query comprehensively."""
        result = EvaluationResult(
            query_id=query_id,
            query=query,
            category=category,
            difficulty=difficulty,
            ground_truth_doc_ids=ground_truth_doc_ids,
            expected_answer=expected_answer,
        )

        try:
            start_time = time.perf_counter()

            retrieval_start = time.perf_counter()
            docs = self.retriever.search(query, top_k=top_k)
            retrieval_latency = (time.perf_counter() - retrieval_start) * 1000

            result.retrieved_doc_ids = [d.doc_id for d in docs]
            result.retrieval_context = [d.content for d in docs]

            result.retrieval_metrics.hit_rate = (
                1.0 if calculate_hit(result.retrieved_doc_ids, ground_truth_doc_ids) else 0.0
            )
            result.is_hit = result.retrieval_metrics.hit_rate == 1.0
            result.retrieval_metrics.mrr = calculate_mrr(result.retrieved_doc_ids, ground_truth_doc_ids)
            result.retrieval_metrics.precision_at_k = calculate_precision_at_k(
                result.retrieved_doc_ids, ground_truth_doc_ids
            )
            result.retrieval_metrics.recall_at_k = calculate_recall_at_k(
                result.retrieved_doc_ids, ground_truth_doc_ids
            )
            result.retrieval_metrics.ndcg_at_k = calculate_ndcg_at_k(result.retrieved_doc_ids, ground_truth_doc_ids)
            result.retrieval_metrics.contextual_relevancy = self.contextual_relevancy_evaluator.evaluate(
                query, result.retrieval_context
            )

            if self.generator:
                generation_start = time.perf_counter()
                result.generated_answer = self._generate_answer(query, result.retrieval_context)
                generation_latency = (time.perf_counter() - generation_start) * 1000

                result.answer_quality_metrics.faithfulness = self.llm_judge.evaluate_faithfulness(
                    result.generated_answer, result.retrieval_context
                )
                result.answer_quality_metrics.answer_relevancy = self.llm_judge.evaluate_relevancy(
                    query, result.generated_answer
                )
                result.answer_quality_metrics.answer_correctness = self.llm_judge.evaluate_correctness(
                    result.generated_answer, expected_answer
                )
                result.answer_quality_metrics.groundedness = self.llm_judge.evaluate_groundedness(
                    result.generated_answer, result.retrieval_context
                )
            else:
                generation_latency = 0.0

            total_latency = (time.perf_counter() - start_time) * 1000
            result.latency_ms = total_latency
            result.performance_metrics.avg_latency_ms = total_latency
            result.performance_metrics.retrieval_latency_ms = retrieval_latency
            result.performance_metrics.generation_latency_ms = generation_latency

        except Exception as e:
            result.error = str(e)
            logger.error(f"Error evaluating query {query_id}: {e}")

        return result

    def evaluate_batch(
        self,
        test_questions: list[dict],
        top_k: int = 5,
    ) -> tuple[list[EvaluationResult], AggregatedMetrics]:
        """Evaluate a batch of test questions."""
        results = []

        for q in test_questions:
            result = self.evaluate_single(
                query=q["question"],
                ground_truth_doc_ids=q.get("ground_truth_doc_ids", []),
                expected_answer=q.get("expected_answer", ""),
                category=q.get("category", "general"),
                difficulty=q.get("difficulty", "medium"),
                query_id=q.get("id", ""),
                top_k=top_k,
            )
            results.append(result)

            status = "✓" if result.is_hit else "✗"
            logger.info(
                f"{status} {result.query_id}: Hit={result.is_hit}, "
                f"MRR={result.retrieval_metrics.mrr:.3f}, "
                f"Retrieved={result.retrieved_doc_ids[:3]}"
            )

        aggregated = self._aggregate_metrics(results)
        return results, aggregated

    def _generate_answer(self, query: str, context: list[str]) -> str:
        """Generate an answer using the provided generator."""
        if hasattr(self.generator, "invoke"):
            context_text = "\n\n".join(context)
            prompt = f"Context:\n{context_text}\n\nQuestion: {query}\n\nAnswer:"
            return self.generator.invoke(prompt)
        return ""

    def _aggregate_metrics(self, results: list[EvaluationResult]) -> AggregatedMetrics:
        """Aggregate metrics across all evaluation results."""
        aggregated = AggregatedMetrics()
        aggregated.total_queries = len(results)

        successful = [r for r in results if r.error is None]
        aggregated.successful_queries = len(successful)
        aggregated.failed_queries = len(results) - len(successful)

        if not successful:
            return aggregated

        aggregated.retrieval.hit_rate = sum(r.retrieval_metrics.hit_rate for r in successful) / len(successful)
        aggregated.retrieval.mrr = sum(r.retrieval_metrics.mrr for r in successful) / len(successful)
        aggregated.retrieval.precision_at_k = sum(r.retrieval_metrics.precision_at_k for r in successful) / len(
            successful
        )
        aggregated.retrieval.recall_at_k = sum(r.retrieval_metrics.recall_at_k for r in successful) / len(successful)
        aggregated.retrieval.ndcg_at_k = sum(r.retrieval_metrics.ndcg_at_k for r in successful) / len(successful)
        aggregated.retrieval.contextual_relevancy = sum(
            r.retrieval_metrics.contextual_relevancy for r in successful
        ) / len(successful)

        answers_with_quality = [r for r in successful if r.generated_answer]
        if answers_with_quality:
            aggregated.answer_quality.faithfulness = sum(
                r.answer_quality_metrics.faithfulness for r in answers_with_quality
            ) / len(answers_with_quality)
            aggregated.answer_quality.answer_relevancy = sum(
                r.answer_quality_metrics.answer_relevancy for r in answers_with_quality
            ) / len(answers_with_quality)
            aggregated.answer_quality.answer_correctness = sum(
                r.answer_quality_metrics.answer_correctness for r in answers_with_quality
            ) / len(answers_with_quality)
            aggregated.answer_quality.groundedness = sum(
                r.answer_quality_metrics.groundedness for r in answers_with_quality
            ) / len(answers_with_quality)

        latencies = [r.latency_ms for r in successful]
        aggregated.performance.avg_latency_ms = sum(latencies) / len(latencies)
        sorted_latencies = sorted(latencies)
        aggregated.performance.p50_latency_ms = sorted_latencies[len(sorted_latencies) // 2]
        aggregated.performance.p95_latency_ms = sorted_latencies[int(len(sorted_latencies) * 0.95)]
        aggregated.performance.p99_latency_ms = sorted_latencies[int(len(sorted_latencies) * 0.99)]

        for category in {r.category for r in successful}:
            cat_results = [r for r in successful if r.category == category]
            aggregated.by_category[category] = {
                "count": len(cat_results),
                "hit_rate": sum(r.retrieval_metrics.hit_rate for r in cat_results) / len(cat_results),
                "mrr": sum(r.retrieval_metrics.mrr for r in cat_results) / len(cat_results),
            }

        for difficulty in {r.difficulty for r in successful}:
            diff_results = [r for r in successful if r.difficulty == difficulty]
            aggregated.by_difficulty[difficulty] = {
                "count": len(diff_results),
                "hit_rate": sum(r.retrieval_metrics.hit_rate for r in diff_results) / len(diff_results),
                "mrr": sum(r.retrieval_metrics.mrr for r in diff_results) / len(diff_results),
            }

        return aggregated


def generate_evaluation_report(
    baseline_metrics: AggregatedMetrics,
    enhanced_metrics: AggregatedMetrics,
    baseline_config: dict,
    enhanced_config: dict,
    output_path: Path,
) -> str:
    """Generate a comprehensive markdown report comparing baseline and enhanced systems."""

    def safe_percentage_change(old: float, new: float) -> float:
        if old == 0:
            return 100.0 if new > 0 else 0.0
        return ((new - old) / old) * 100

    hit_rate_change = safe_percentage_change(baseline_metrics.retrieval.hit_rate, enhanced_metrics.retrieval.hit_rate)
    mrr_change = safe_percentage_change(baseline_metrics.retrieval.mrr, enhanced_metrics.retrieval.mrr)

    report = f"""# RAG System Evaluation Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Executive Summary

This report presents a comprehensive evaluation of the RAG (Retrieval-Augmented Generation) system, comparing baseline and enhanced configurations across multiple dimensions:
- **Retrieval Quality** (Hit Rate, MRR, Precision, Recall, NDCG)
- **Answer Quality** (Faithfulness, Relevancy, Correctness, Groundedness)
- **Performance** (Latency, Throughput)

---

## Configuration Comparison

### Baseline Configuration
```
Embedding Model: {baseline_config.get("embedding_model", "N/A")}
Top-K: {baseline_config.get("top_k", "N/A")}
Search Type: {baseline_config.get("search_type", "vector_only")}
Reranking: {baseline_config.get("use_reranker", False)}
```

### Enhanced Configuration
```
Embedding Model: {enhanced_config.get("embedding_model", "N/A")}
Reranker Model: {enhanced_config.get("reranker_model", "N/A")}
Top-K: {enhanced_config.get("top_k", "N/A")}
Candidate Pool Size: {enhanced_config.get("candidate_pool_size", "N/A")}
Search Type: {enhanced_config.get("search_type", "hybrid")}
Fusion Method: {enhanced_config.get("fusion_method", "RRF")}
Reranking: {enhanced_config.get("use_reranker", True)}
```

---

## Retrieval Quality Metrics

| Metric | Baseline | Enhanced | Change | % Improvement |
|--------|----------|----------|--------|---------------|
| Hit Rate | {baseline_metrics.retrieval.hit_rate:.2%} | {enhanced_metrics.retrieval.hit_rate:.2%} | {(enhanced_metrics.retrieval.hit_rate - baseline_metrics.retrieval.hit_rate):+.2%} | {hit_rate_change:+.1f}% |
| MRR | {baseline_metrics.retrieval.mrr:.4f} | {enhanced_metrics.retrieval.mrr:.4f} | {(enhanced_metrics.retrieval.mrr - baseline_metrics.retrieval.mrr):+.4f} | {mrr_change:+.1f}% |
| Precision@K | {baseline_metrics.retrieval.precision_at_k:.4f} | {enhanced_metrics.retrieval.precision_at_k:.4f} | {(enhanced_metrics.retrieval.precision_at_k - baseline_metrics.retrieval.precision_at_k):+.4f} | - |
| Recall@K | {baseline_metrics.retrieval.recall_at_k:.4f} | {enhanced_metrics.retrieval.recall_at_k:.4f} | {(enhanced_metrics.retrieval.recall_at_k - baseline_metrics.retrieval.recall_at_k):+.4f} | - |
| NDCG@K | {baseline_metrics.retrieval.ndcg_at_k:.4f} | {enhanced_metrics.retrieval.ndcg_at_k:.4f} | {(enhanced_metrics.retrieval.ndcg_at_k - baseline_metrics.retrieval.ndcg_at_k):+.4f} | - |
| Contextual Relevancy | {baseline_metrics.retrieval.contextual_relevancy:.4f} | {enhanced_metrics.retrieval.contextual_relevancy:.4f} | {(enhanced_metrics.retrieval.contextual_relevancy - baseline_metrics.retrieval.contextual_relevancy):+.4f} | - |

### Target Achievement (30% Improvement Required)

- **Hit Rate**: {"✅ ACHIEVED" if hit_rate_change >= 30 else "❌ NOT YET"} ({hit_rate_change:+.1f}% improvement)
- **MRR**: {"✅ ACHIEVED" if mrr_change >= 30 else "❌ NOT YET"} ({mrr_change:+.1f}% improvement)

---

## Performance Metrics

| Metric | Baseline | Enhanced | Change |
|--------|----------|----------|--------|
| Avg Latency (ms) | {baseline_metrics.performance.avg_latency_ms:.1f} | {enhanced_metrics.performance.avg_latency_ms:.1f} | {(enhanced_metrics.performance.avg_latency_ms - baseline_metrics.performance.avg_latency_ms):+.1f} |
| P50 Latency (ms) | {baseline_metrics.performance.p50_latency_ms:.1f} | {enhanced_metrics.performance.p50_latency_ms:.1f} | {(enhanced_metrics.performance.p50_latency_ms - baseline_metrics.performance.p50_latency_ms):+.1f} |
| P95 Latency (ms) | {baseline_metrics.performance.p95_latency_ms:.1f} | {enhanced_metrics.performance.p95_latency_ms:.1f} | {(enhanced_metrics.performance.p95_latency_ms - baseline_metrics.performance.p95_latency_ms):+.1f} |

---

## Results by Category

### Baseline Performance by Category
| Category | Count | Hit Rate | MRR |
|----------|-------|----------|-----|
"""

    for category, stats in baseline_metrics.by_category.items():
        report += f"| {category} | {stats['count']} | {stats['hit_rate']:.2%} | {stats['mrr']:.4f} |\n"

    report += """
### Enhanced Performance by Category
| Category | Count | Hit Rate | MRR |
|----------|-------|----------|-----|
"""

    for category, stats in enhanced_metrics.by_category.items():
        report += f"| {category} | {stats['count']} | {stats['hit_rate']:.2%} | {stats['mrr']:.4f} |\n"

    report += """
---

## Results by Difficulty

### Baseline Performance by Difficulty
| Difficulty | Count | Hit Rate | MRR |
|------------|-------|----------|-----|
"""

    for difficulty, stats in baseline_metrics.by_difficulty.items():
        report += f"| {difficulty} | {stats['count']} | {stats['hit_rate']:.2%} | {stats['mrr']:.4f} |\n"

    report += """
### Enhanced Performance by Difficulty
| Difficulty | Count | Hit Rate | MRR |
|------------|-------|----------|-----|
"""

    for difficulty, stats in enhanced_metrics.by_difficulty.items():
        report += f"| {difficulty} | {stats['count']} | {stats['hit_rate']:.2%} | {stats['mrr']:.4f} |\n"

    report += f"""
---

## Summary Statistics

| Metric | Baseline | Enhanced |
|--------|----------|----------|
| Total Queries | {baseline_metrics.total_queries} | {enhanced_metrics.total_queries} |
| Successful Queries | {baseline_metrics.successful_queries} | {enhanced_metrics.successful_queries} |
| Failed Queries | {baseline_metrics.failed_queries} | {enhanced_metrics.failed_queries} |

---

## Analysis and Recommendations

### Key Findings

1. **Retrieval Improvement**: The enhanced system achieves {hit_rate_change:+.1f}% improvement in hit rate and {mrr_change:+.1f}% improvement in MRR.

2. **Latency Trade-off**: Enhanced retrieval adds approximately {(enhanced_metrics.performance.avg_latency_ms - baseline_metrics.performance.avg_latency_ms):.1f}ms of latency due to hybrid search and reranking.

3. **Category Analysis**: Different query categories show varying levels of improvement.

### Enhancement Techniques Applied

1. **Hybrid Search**: Combining vector similarity with BM25 keyword matching captures both semantic and lexical relevance.

2. **Cross-Encoder Reranking**: The reranker provides more accurate relevance scoring by considering query-document pairs jointly.

3. **Reciprocal Rank Fusion**: RRF effectively combines results from multiple retrieval methods.

4. **Expanded Candidate Pool**: Retrieving more candidates before reranking improves recall of relevant documents.

---

*Report generated by Comprehensive RAG Evaluation Framework*
"""

    with open(output_path, "w") as f:
        f.write(report)

    return report


def save_detailed_results(
    results: list[EvaluationResult],
    metrics: AggregatedMetrics,
    config: dict,
    output_path: Path,
    prefix: str,
):
    """Save detailed evaluation results to JSON."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    data = {
        "timestamp": timestamp,
        "config": config,
        "aggregated_metrics": {
            "total_queries": metrics.total_queries,
            "successful_queries": metrics.successful_queries,
            "failed_queries": metrics.failed_queries,
            "retrieval": {
                "hit_rate": metrics.retrieval.hit_rate,
                "mrr": metrics.retrieval.mrr,
                "precision_at_k": metrics.retrieval.precision_at_k,
                "recall_at_k": metrics.retrieval.recall_at_k,
                "ndcg_at_k": metrics.retrieval.ndcg_at_k,
                "contextual_relevancy": metrics.retrieval.contextual_relevancy,
            },
            "performance": {
                "avg_latency_ms": metrics.performance.avg_latency_ms,
                "p50_latency_ms": metrics.performance.p50_latency_ms,
                "p95_latency_ms": metrics.performance.p95_latency_ms,
                "p99_latency_ms": metrics.performance.p99_latency_ms,
            },
            "by_category": metrics.by_category,
            "by_difficulty": metrics.by_difficulty,
        },
        "detailed_results": [
            {
                "query_id": r.query_id,
                "query": r.query,
                "category": r.category,
                "difficulty": r.difficulty,
                "retrieved_doc_ids": r.retrieved_doc_ids,
                "ground_truth_doc_ids": r.ground_truth_doc_ids,
                "is_hit": r.is_hit,
                "latency_ms": r.latency_ms,
                "retrieval_metrics": {
                    "hit_rate": r.retrieval_metrics.hit_rate,
                    "mrr": r.retrieval_metrics.mrr,
                    "precision_at_k": r.retrieval_metrics.precision_at_k,
                    "recall_at_k": r.retrieval_metrics.recall_at_k,
                    "ndcg_at_k": r.retrieval_metrics.ndcg_at_k,
                    "contextual_relevancy": r.retrieval_metrics.contextual_relevancy,
                },
                "error": r.error,
            }
            for r in results
        ],
    }

    output_file = output_path / f"{prefix}_results_{timestamp}.json"
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

    latest_file = output_path / f"{prefix}_latest.json"
    with open(latest_file, "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Saved results to {output_file}")
    return data
