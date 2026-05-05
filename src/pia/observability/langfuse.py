"""Thin Langfuse adapter.

If ``LANGFUSE_PUBLIC_KEY`` is unset (or ``langfuse`` is not installed),
decorated calls run without tracing. The adapter works identically in both
code paths so unit tests never need Langfuse credentials.

Langfuse SDK version requirement: ``>=2.50`` (actual: 4.5.1 at time of
writing).  The adapter uses ``Langfuse.start_as_current_observation(name=)``
which is the stable context-manager API in this version family.
``start_as_current_span`` does **not** exist in langfuse 4.x — do not use it.

Per-request trace correlation: callers (e.g. ``planner.advise``) set a
request id via :func:`set_request_id` before invoking decorated work; the
:func:`trace` decorator reads the context var and passes ``trace_context``
into ``start_as_current_observation`` so all nested spans roll up under one
trace in the Langfuse dashboard. Without an explicit id, Langfuse generates
its own per-span ids and the SDK's parent-child context still nests them
correctly — the contextvar is purely for naming the top-level trace.
"""

from __future__ import annotations

import functools
import os
from collections.abc import Callable
from contextvars import ContextVar, Token
from typing import Any

_client: Any | None = None
_client_config: tuple[str, str, str] | None = None
_request_id_var: ContextVar[str | None] = ContextVar("pia_request_id", default=None)


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


def set_request_id(request_id: str | None) -> Token:
    """Bind a trace id to the current contextvars context. Use the returned
    Token with :func:`reset_request_id` to clear it on exit."""
    return _request_id_var.set(request_id)


def reset_request_id(token: Token) -> None:
    _request_id_var.reset(token)


def current_request_id() -> str | None:
    return _request_id_var.get()


def trace(name: str) -> Callable:
    """Decorator that wraps a function in a Langfuse observation span.

    When Langfuse keys are unset or the package is unavailable, the wrapper
    simply calls the original function. When a request id is bound via
    :func:`set_request_id`, it is forwarded as the Langfuse trace id so
    every nested span lands under the same trace in the dashboard.
    """

    def deco(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            client = _get_client()
            if client is None:
                return fn(*args, **kwargs)
            request_id = _request_id_var.get()
            cm_kwargs: dict[str, Any] = {"name": name}
            if request_id:
                cm_kwargs["trace_context"] = {"trace_id": request_id}
            with client.start_as_current_observation(**cm_kwargs):
                return fn(*args, **kwargs)

        return wrapped

    return deco
