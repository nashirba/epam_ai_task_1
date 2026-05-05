"""Tests for the in-process metrics registry."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from pia.agents.planner import advise
from pia.observability.metrics import Histogram, get_registry, record_call
from pia.safety.guardrail import guardrail_output


@pytest.fixture(autouse=True)
def _reset_registry():
    get_registry().reset()
    yield
    get_registry().reset()


def test_counter_increments_atomically():
    counter = get_registry().counter("test.counter")
    counter.inc()
    counter.inc(3)
    assert get_registry().counter("test.counter").value == 4


def test_histogram_percentile_basic():
    h = Histogram(name="t")
    for v in (0.1, 0.2, 0.3, 0.4, 0.5):
        h.observe(v)
    assert h.count == 5
    p50 = h.percentile(0.5)
    p95 = h.percentile(0.95)
    assert p50 is not None and p95 is not None
    assert p50 <= p95


def test_record_call_counts_calls_and_errors():
    with record_call("worker.task"):
        pass
    with pytest.raises(ValueError, match="boom"), record_call("worker.task"):
        raise ValueError("boom")
    registry = get_registry()
    assert registry.counter("worker.task.calls").value == 2
    assert registry.counter("worker.task.errors").value == 1
    latency = registry.histogram("worker.task.latency_s")
    assert latency.count == 2


def test_advise_records_metrics_and_request_id():
    with patch("pia.agents.planner._make_planner") as mp:
        mp.return_value.run.return_value.text = "Hold."
        # First call
        advise("first question")
        # Second call
        advise("second question")
    registry = get_registry()
    assert registry.counter("advise.calls").value == 2
    assert registry.counter("advise.errors").value == 0
    assert registry.histogram("advise.latency_s").count == 2
    assert registry.last_request_id is not None
    # Request id is a uuid4 hex (32 chars).
    assert len(registry.last_request_id) == 32


def test_guardrail_records_redaction_and_hedge():
    out = guardrail_output("Password is hunter2 and you must buy HSBK now")
    assert "[REDACTED]" in out
    assert out.startswith("Hedged note: ")
    registry = get_registry()
    assert registry.counter("guardrail.redaction_fired").value == 1
    assert registry.counter("guardrail.hedge_fired").value == 1
