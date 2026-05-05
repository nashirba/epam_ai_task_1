"""Per-request MCP session pool.

In v1 every ``kz_data_call_sync`` spawned a fresh subprocess: a single
``advise()`` run with 3-5 tool calls paid 3-5x the FastMCP startup cost,
which dominates latency. This module exposes a sync facade that owns one
stdio subprocess + one ``ClientSession`` for the lifetime of one request,
backed by a daemon thread running its own asyncio loop. Tool calls dispatch
onto that loop via :func:`asyncio.run_coroutine_threadsafe`.

Activation is opt-in via :func:`bind_kz_data_session`, which sets a
``ContextVar``. The :func:`pia.mcp.client.kz_data_call_sync` function reads
the var; when set, it routes through the active session, otherwise it falls
back to the original spawn-per-call path so unit tests and ad-hoc CLI calls
keep working.

Web search (Tavily) is not pooled in v1 — it spawns ``npx`` from a different
binary and is called at most once per request anyway.
"""

from __future__ import annotations

import asyncio
import sys
import threading
from contextvars import ContextVar, Token
from typing import Any

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from pia.config import get_settings

_OPEN_TIMEOUT_S = 30
_CALL_TIMEOUT_S = 60


class MCPSessionSync:
    """Sync facade owning one async MCP stdio session.

    Use as a context manager; only one instance per request is supported.
    """

    def __init__(self, params: StdioServerParameters) -> None:
        self._params = params
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._session: ClientSession | None = None
        self._stop_holder: list[asyncio.Event] = []
        self._opened = threading.Event()
        self._open_error: BaseException | None = None

    def _runner(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop

        async def lifetime() -> None:
            self._stop_holder.append(asyncio.Event())
            try:
                async with (
                    stdio_client(self._params) as (read, write),
                    ClientSession(read, write) as session,
                ):
                    await session.initialize()
                    self._session = session
                    self._opened.set()
                    await self._stop_holder[0].wait()
            except BaseException as exc:
                self._open_error = exc
                self._opened.set()
                raise

        try:
            loop.run_until_complete(lifetime())
        finally:
            loop.close()

    def __enter__(self) -> MCPSessionSync:
        self._thread = threading.Thread(target=self._runner, daemon=True)
        self._thread.start()
        if not self._opened.wait(timeout=_OPEN_TIMEOUT_S):
            raise TimeoutError(
                f"MCP session failed to open within {_OPEN_TIMEOUT_S}s"
            )
        if self._open_error is not None:
            raise self._open_error
        return self

    def call(self, tool_name: str, **kwargs: Any) -> Any:
        if self._session is None or self._loop is None:
            raise RuntimeError("MCPSessionSync not entered")
        future = asyncio.run_coroutine_threadsafe(
            self._session.call_tool(tool_name, arguments=kwargs),
            self._loop,
        )
        result = future.result(timeout=_CALL_TIMEOUT_S)
        return result.content[0].text if result.content else None

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self._loop is not None and self._stop_holder:
            self._loop.call_soon_threadsafe(self._stop_holder[0].set)
        if self._thread is not None:
            self._thread.join(timeout=10)


_active_kz_data: ContextVar[MCPSessionSync | None] = ContextVar(
    "pia_active_kz_data_session", default=None
)


def bind_kz_data_session(session: MCPSessionSync | None) -> Token:
    """Make ``session`` the active kz-data session for the current context."""
    return _active_kz_data.set(session)


def reset_kz_data_session(token: Token) -> None:
    _active_kz_data.reset(token)


def active_kz_data_session() -> MCPSessionSync | None:
    return _active_kz_data.get()


def kz_data_params() -> StdioServerParameters:
    settings = get_settings()
    return StdioServerParameters(
        command=sys.executable,
        args=[settings.kz_data_mcp_path],
    )
