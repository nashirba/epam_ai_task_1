"""In-process metrics registry for PIA.

Single-user local runtime — Prometheus would be massive overkill. The
registry is a thread-safe, process-global accumulator of counters and
histograms, plus a "last trace id" pointer so the Streamlit diagnostics
view can deep-link into Langfuse.

Counters track: ``advise.calls``, ``advise.errors``, ``mcp.kz_data.calls``,
``mcp.kz_data.errors``, ``mcp.web_search.calls``, ``rag.retrieve.calls``,
``llm.chat.calls``, ``guardrail.hedge_fired``, ``guardrail.redaction_fired``.

Histograms track latency in seconds for the same set, with p50/p95
percentiles computed on demand via :func:`Histogram.percentile`.

This module is import-side-effect-free. Wiring to ``@trace``-decorated
functions happens via :func:`record_call` — call it inside a context
manager that times the wrapped block.
"""

from __future__ import annotations

import threading
import time
from bisect import insort
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field

_lock = threading.Lock()


@dataclass
class Counter:
    name: str
    value: int = 0

    def inc(self, n: int = 1) -> None:
        with _lock:
            self.value += n


@dataclass
class Histogram:
    name: str
    samples: list[float] = field(default_factory=list)

    def observe(self, seconds: float) -> None:
        with _lock:
            insort(self.samples, seconds)

    def percentile(self, q: float) -> float | None:
        with _lock:
            if not self.samples:
                return None
            k = max(0, min(len(self.samples) - 1, round(q * (len(self.samples) - 1))))
            return self.samples[k]

    @property
    def count(self) -> int:
        return len(self.samples)


@dataclass
class Registry:
    counters: dict[str, Counter] = field(default_factory=dict)
    histograms: dict[str, Histogram] = field(default_factory=dict)
    last_request_id: str | None = None

    def counter(self, name: str) -> Counter:
        with _lock:
            if name not in self.counters:
                self.counters[name] = Counter(name=name)
            return self.counters[name]

    def histogram(self, name: str) -> Histogram:
        with _lock:
            if name not in self.histograms:
                self.histograms[name] = Histogram(name=name)
            return self.histograms[name]

    def set_last_request_id(self, request_id: str | None) -> None:
        with _lock:
            self.last_request_id = request_id

    def reset(self) -> None:
        with _lock:
            self.counters.clear()
            self.histograms.clear()
            self.last_request_id = None


_registry = Registry()


def get_registry() -> Registry:
    return _registry


@contextmanager
def record_call(name: str) -> Iterator[None]:
    """Time a code block and increment ``<name>.calls``; on exception also
    increment ``<name>.errors`` and re-raise."""
    started = time.perf_counter()
    _registry.counter(f"{name}.calls").inc()
    try:
        yield
    except BaseException:
        _registry.counter(f"{name}.errors").inc()
        raise
    finally:
        _registry.histogram(f"{name}.latency_s").observe(time.perf_counter() - started)
