"""Thin Langfuse adapter.

If ``LANGFUSE_PUBLIC_KEY`` is unset (or ``langfuse`` is not installed),
decorated calls run without tracing. The adapter works identically in both
code paths so unit tests never need Langfuse credentials.

Langfuse SDK version requirement: ``>=2.50`` (actual: 4.5.1 at time of
writing).  The adapter uses ``Langfuse.start_as_current_observation(name=)``
which is the stable context-manager API in this version family.
``start_as_current_span`` does **not** exist in langfuse 4.x — do not use it.
"""

from __future__ import annotations

import functools
import os
from collections.abc import Callable
from typing import Any

_client: Any | None = None
_client_config: tuple[str, str, str] | None = None


def _get_client() -> Any | None:
    """Lazily initialize Langfuse from environment variables."""
    global _client, _client_config

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    if not public_key or not secret_key:
        return None

    config = (public_key, secret_key, host)
    if _client is not None and _client_config == config:
        return _client

    try:
        from langfuse import Langfuse
    except ImportError:
        return None

    _client = Langfuse(public_key=public_key, secret_key=secret_key, host=host)
    _client_config = config
    return _client


def trace(name: str) -> Callable:
    """Decorator that wraps a function in a Langfuse observation span.

    When Langfuse keys are unset or the package is unavailable, the wrapper
    simply calls the original function.
    """

    def deco(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            client = _get_client()
            if client is None:
                return fn(*args, **kwargs)
            with client.start_as_current_observation(name=name):
                return fn(*args, **kwargs)

        return wrapped

    return deco
