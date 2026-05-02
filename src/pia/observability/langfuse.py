"""Thin Langfuse adapter.

If ``LANGFUSE_PUBLIC_KEY`` is unset (or ``langfuse`` is not installed),
every decorator is a true no-op that adds zero overhead to the wrapped
function.  The adapter works identically in both code paths so unit tests
never need Langfuse credentials.

Langfuse SDK version requirement: ``>=2.50`` (actual: 4.5.1 at time of
writing).  The adapter uses ``Langfuse.start_as_current_observation(name=)``
which is the stable context-manager API in this version family.
``start_as_current_span`` does **not** exist in langfuse 4.x — do not use it.
"""
from __future__ import annotations

import functools
import os
from typing import Any, Callable

try:
    from langfuse import Langfuse as _LangfuseClass

    _client: _LangfuseClass | None = None
    if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
        _client = _LangfuseClass(
            public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
            secret_key=os.environ["LANGFUSE_SECRET_KEY"],
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )
except ImportError:  # langfuse not installed in dev path
    _client = None


def trace(name: str) -> Callable:
    """Decorator that wraps a function in a Langfuse observation span.

    When ``_client is None`` (keys unset or langfuse not installed) the
    decorator returns the original function unchanged — no wrapping, no
    overhead.
    """

    def deco(fn: Callable) -> Callable:
        if _client is None:
            # True no-op: return the function itself, not a wrapper.
            return fn

        @functools.wraps(fn)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            with _client.start_as_current_observation(name=name):  # type: ignore[union-attr]
                return fn(*args, **kwargs)

        return wrapped

    return deco
