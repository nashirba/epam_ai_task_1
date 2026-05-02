# tests/integration/test_retrieval_metric.py
from pathlib import Path

import pytest
import yaml

from pia.eval.retrieval import evaluate_retrieval, hit_rate_at_k


@pytest.mark.integration
def test_retrieval_at_5_above_threshold():
    cases = yaml.safe_load(Path("tests/fixtures/retrieval_labels.yaml").read_text())
    results = evaluate_retrieval(cases, k=5)
    p = hit_rate_at_k(results)
    assert p >= 0.6, f"hit_rate@5={p:.2f} below 0.6 threshold; misses: " + ", ".join(
        r.query for r in results if not r.hit_at_k
    )
