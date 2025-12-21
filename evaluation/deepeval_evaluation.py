"""
DeepEval-based RAG Evaluation

This module provides integration with DeepEval framework for comprehensive
RAG evaluation using LLM-as-a-Judge metrics.

Reference: https://github.com/confident-ai/deepeval

Note: This requires OpenAI API key for LLM-based evaluation.
Set OPENAI_API_KEY environment variable before running.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from deepeval.metrics import (
        AnswerRelevancyMetric,
        ContextualPrecisionMetric,
        ContextualRecallMetric,
        ContextualRelevancyMetric,
        FaithfulnessMetric,
        GEval,
    )
    from deepeval.test_case import LLMTestCase, LLMTestCaseParams

    DEEPEVAL_AVAILABLE = True
except ImportError:
    DEEPEVAL_AVAILABLE = False
    logger.warning("DeepEval not installed. Install with: pip install deepeval")


def create_rag_test_case(
    query: str,
    actual_output: str,
    retrieval_context: list[str],
    expected_output: str | None = None,
) -> "LLMTestCase":
    """Create a DeepEval test case for RAG evaluation."""
    if not DEEPEVAL_AVAILABLE:
        raise ImportError("DeepEval is not installed")

    return LLMTestCase(
        input=query,
        actual_output=actual_output,
        retrieval_context=retrieval_context,
        expected_output=expected_output,
    )


def create_rag_metrics(
    threshold: float = 0.5,
    include_retrieval: bool = True,
    include_generation: bool = True,
    model: str = "gpt-4o-mini",
) -> list[Any]:
    """
    Create a set of RAG evaluation metrics.

    Args:
        threshold: Minimum passing score (0-1)
        include_retrieval: Include retrieval-focused metrics
        include_generation: Include generation-focused metrics
        model: LLM model for evaluation

    Returns:
        List of DeepEval metrics
    """
    if not DEEPEVAL_AVAILABLE:
        raise ImportError("DeepEval is not installed")

    metrics = []

    if include_retrieval:
        metrics.append(
            ContextualRelevancyMetric(
                threshold=threshold,
                model=model,
                include_reason=True,
            )
        )

        metrics.append(
            ContextualPrecisionMetric(
                threshold=threshold,
                model=model,
                include_reason=True,
            )
        )

        metrics.append(
            ContextualRecallMetric(
                threshold=threshold,
                model=model,
                include_reason=True,
            )
        )

    if include_generation:
        metrics.append(
            FaithfulnessMetric(
                threshold=threshold,
                model=model,
                include_reason=True,
            )
        )

        metrics.append(
            AnswerRelevancyMetric(
                threshold=threshold,
                model=model,
                include_reason=True,
            )
        )

    return metrics


def create_custom_metric(
    name: str,
    criteria: str,
    evaluation_params: list | None = None,
    threshold: float = 0.5,
) -> "GEval":
    """
    Create a custom G-Eval metric.

    Args:
        name: Name of the metric
        criteria: Evaluation criteria in natural language
        evaluation_params: List of test case parameters to use
        threshold: Minimum passing score

    Returns:
        GEval metric instance
    """
    if not DEEPEVAL_AVAILABLE:
        raise ImportError("DeepEval is not installed")

    if evaluation_params is None:
        evaluation_params = [LLMTestCaseParams.ACTUAL_OUTPUT]

    return GEval(
        name=name,
        criteria=criteria,
        evaluation_params=evaluation_params,
        threshold=threshold,
    )


def evaluate_rag_response(
    query: str,
    response: str,
    retrieval_context: list[str],
    expected_output: str | None = None,
    metrics: list[Any] | None = None,
) -> dict:
    """
    Evaluate a single RAG response using DeepEval metrics.

    Args:
        query: User query
        response: Generated response
        retrieval_context: List of retrieved text chunks
        expected_output: Expected/gold answer (optional)
        metrics: List of metrics to use (default: all RAG metrics)

    Returns:
        Dictionary with evaluation results
    """
    if not DEEPEVAL_AVAILABLE:
        raise ImportError("DeepEval is not installed")

    test_case = create_rag_test_case(
        query=query,
        actual_output=response,
        retrieval_context=retrieval_context,
        expected_output=expected_output,
    )

    if metrics is None:
        metrics = create_rag_metrics()

    results = {}
    for metric in metrics:
        try:
            metric.measure(test_case)
            results[metric.__class__.__name__] = {
                "score": metric.score,
                "reason": getattr(metric, "reason", None),
                "threshold": metric.threshold,
                "passed": metric.score >= metric.threshold,
            }
        except Exception as e:
            logger.warning(f"Metric {metric.__class__.__name__} failed: {e}")
            results[metric.__class__.__name__] = {"error": str(e)}

    return results


def run_deepeval_evaluation(
    retriever: Any,
    generator: Any,
    test_questions: list[dict],
    top_k: int = 5,
    model: str = "gpt-4o-mini",
) -> dict:
    """
    Run full DeepEval evaluation on test questions.

    Args:
        retriever: Retriever instance with search() method
        generator: Generator instance for answer generation
        test_questions: List of test question dictionaries
        top_k: Number of documents to retrieve
        model: LLM model for evaluation

    Returns:
        Dictionary with aggregated evaluation results
    """
    if not DEEPEVAL_AVAILABLE:
        raise ImportError("DeepEval is not installed")

    test_cases = []
    results = []
    metrics = create_rag_metrics(model=model)

    for q in test_questions:
        query = q["question"]
        expected = q.get("expected_answer", "")

        try:
            docs = retriever.search(query, top_k=top_k)
            retrieval_context = [d.content for d in docs]

            context_text = "\n\n".join(retrieval_context)
            prompt = f"Context:\n{context_text}\n\nQuestion: {query}\n\nAnswer:"

            if hasattr(generator, "invoke"):
                response = generator.invoke(prompt)
            else:
                response = "Generated answer placeholder"

            test_case = create_rag_test_case(
                query=query,
                actual_output=response,
                retrieval_context=retrieval_context,
                expected_output=expected if expected else None,
            )
            test_cases.append(test_case)

            query_results = {"query_id": q.get("id", ""), "query": query, "metrics": {}}

            for metric in metrics:
                try:
                    metric.measure(test_case)
                    query_results["metrics"][metric.__class__.__name__] = {
                        "score": metric.score,
                        "passed": metric.score >= metric.threshold,
                    }
                except Exception as e:
                    logger.warning(f"Metric {metric.__class__.__name__} failed: {e}")
                    query_results["metrics"][metric.__class__.__name__] = {"error": str(e)}

            results.append(query_results)

        except Exception as e:
            logger.error(f"Error evaluating query {q.get('id', '')}: {e}")
            results.append({"query_id": q.get("id", ""), "error": str(e)})

    aggregated = aggregate_results(results)
    return {"detailed_results": results, "aggregated": aggregated}


def aggregate_results(results: list[dict]) -> dict:
    """Aggregate evaluation results across all queries."""
    aggregated = {}
    metric_scores = {}

    for result in results:
        if "error" in result:
            continue

        for metric_name, metric_data in result.get("metrics", {}).items():
            if "error" in metric_data:
                continue

            if metric_name not in metric_scores:
                metric_scores[metric_name] = {"scores": [], "passed": 0, "total": 0}

            metric_scores[metric_name]["scores"].append(metric_data["score"])
            metric_scores[metric_name]["total"] += 1
            if metric_data["passed"]:
                metric_scores[metric_name]["passed"] += 1

    for metric_name, data in metric_scores.items():
        if data["scores"]:
            aggregated[metric_name] = {
                "avg_score": sum(data["scores"]) / len(data["scores"]),
                "min_score": min(data["scores"]),
                "max_score": max(data["scores"]),
                "pass_rate": data["passed"] / data["total"] if data["total"] > 0 else 0,
                "total_evaluated": data["total"],
            }

    return aggregated


class DeepEvalRAGEvaluator:
    """
    DeepEval-based RAG evaluator class.

    This provides a structured interface for RAG evaluation using DeepEval metrics.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        threshold: float = 0.5,
    ):
        """
        Initialize the DeepEval RAG evaluator.

        Args:
            model: LLM model for evaluation (requires OpenAI API key)
            threshold: Default passing threshold for metrics
        """
        if not DEEPEVAL_AVAILABLE:
            raise ImportError("DeepEval is not installed. Install with: pip install deepeval")

        self.model = model
        self.threshold = threshold
        self.metrics = create_rag_metrics(
            threshold=threshold,
            model=model,
            include_retrieval=True,
            include_generation=True,
        )

    def evaluate_single(
        self,
        query: str,
        response: str,
        retrieval_context: list[str],
        expected_output: str | None = None,
    ) -> dict:
        """Evaluate a single RAG response."""
        return evaluate_rag_response(
            query=query,
            response=response,
            retrieval_context=retrieval_context,
            expected_output=expected_output,
            metrics=self.metrics,
        )

    def add_custom_metric(
        self,
        name: str,
        criteria: str,
        threshold: float | None = None,
    ):
        """Add a custom G-Eval metric."""
        metric = create_custom_metric(
            name=name,
            criteria=criteria,
            threshold=threshold or self.threshold,
        )
        self.metrics.append(metric)


NUTRITION_METRICS = [
    {
        "name": "Nutritional Accuracy",
        "criteria": "Determine if the nutritional information provided is scientifically accurate and up-to-date based on current dietary guidelines.",
    },
    {
        "name": "Safety Awareness",
        "criteria": "Evaluate whether the response appropriately mentions relevant safety considerations, contraindications, or when to consult healthcare professionals.",
    },
    {
        "name": "Practical Applicability",
        "criteria": "Assess how practical and actionable the dietary advice is for the average person to implement in their daily life.",
    },
]


def create_nutrition_specific_evaluator(
    model: str = "gpt-4o-mini",
    threshold: float = 0.5,
) -> "DeepEvalRAGEvaluator":
    """
    Create a nutrition-domain-specific evaluator with custom metrics.

    Returns:
        DeepEvalRAGEvaluator with nutrition-specific metrics
    """
    evaluator = DeepEvalRAGEvaluator(model=model, threshold=threshold)

    for metric_def in NUTRITION_METRICS:
        evaluator.add_custom_metric(
            name=metric_def["name"],
            criteria=metric_def["criteria"],
        )

    return evaluator


if __name__ == "__main__":
    if not DEEPEVAL_AVAILABLE:
        print("DeepEval is not installed. Install with: pip install deepeval")
        print("Also requires: export OPENAI_API_KEY=your_key")
        sys.exit(1)

    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY environment variable not set")
        print("DeepEval requires OpenAI API for LLM-as-judge evaluation")
        sys.exit(1)

    test_query = "What are the benefits of the Mediterranean diet?"
    test_response = (
        "The Mediterranean diet offers several health benefits including reduced "
        "cardiovascular disease risk, lower inflammation, and improved cognitive function. "
        "It emphasizes olive oil, fruits, vegetables, whole grains, and fish."
    )
    test_context = [
        "The Mediterranean diet is based on traditional eating patterns of countries "
        "bordering the Mediterranean Sea. It emphasizes olive oil as the primary fat source, "
        "abundant fruits and vegetables, whole grains, legumes, nuts, and seeds."
    ]

    print("Running DeepEval RAG evaluation demo...")
    print(f"Query: {test_query}")
    print(f"Response: {test_response[:100]}...")
    print()

    results = evaluate_rag_response(
        query=test_query,
        response=test_response,
        retrieval_context=test_context,
    )

    print("Results:")
    for metric_name, metric_result in results.items():
        if "error" in metric_result:
            print(f"  ❌ {metric_name}: Error - {metric_result['error']}")
        else:
            status = "✅" if metric_result["passed"] else "❌"
            print(f"  {status} {metric_name}: {metric_result['score']:.3f}")
            if metric_result.get("reason"):
                print(f"      Reason: {metric_result['reason'][:100]}...")

    print("\nDeepEval evaluation demo complete!")
