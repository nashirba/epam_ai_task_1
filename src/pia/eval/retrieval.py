# src/pia/eval/retrieval.py
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from pia.rag.retrieve import retrieve


@dataclass(frozen=True)
class RetrievalResult:
    query: str
    hit_at_k: bool
    matched_sources: list[str]
    expected_sources: list[str]


def evaluate_retrieval(cases: Iterable[dict], *, k: int = 5) -> list[RetrievalResult]:
    out: list[RetrievalResult] = []
    for case in cases:
        chunks = retrieve(case["query"], k=k)
        sources = [c.source for c in chunks]
        hit = any(s in sources for s in case["expected_sources"])
        out.append(
            RetrievalResult(
                query=case["query"],
                hit_at_k=hit,
                matched_sources=[s for s in sources if s in case["expected_sources"]],
                expected_sources=case["expected_sources"],
            )
        )
    return out


def precision_at_k(results: list[RetrievalResult]) -> float:
    if not results:
        return 0.0
    return sum(1 for r in results if r.hit_at_k) / len(results)
