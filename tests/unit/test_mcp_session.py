"""MCP session pool unit tests.

These tests exercise the contextvar routing and best-effort fallback that
``MCPSessionSync`` provides, without spawning a real FastMCP subprocess —
the integration test ``tests/integration/test_mcp.py`` already covers the
real-subprocess round trip.
"""

from __future__ import annotations

import pytest

from pia.mcp.client import kz_data_call_sync
from pia.mcp.session import (
    active_kz_data_session,
    bind_kz_data_session,
    reset_kz_data_session,
)


class _FakePooledSession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def call(self, tool_name: str, **kwargs: object) -> str:
        self.calls.append((tool_name, dict(kwargs)))
        return f"pooled:{tool_name}"


def test_kz_data_call_routes_through_active_session():
    fake = _FakePooledSession()
    token = bind_kz_data_session(fake)  # type: ignore[arg-type]
    try:
        out = kz_data_call_sync("get_nbk_rate", date_str="2026-01-01")
    finally:
        reset_kz_data_session(token)
    assert out == "pooled:get_nbk_rate"
    assert fake.calls == [("get_nbk_rate", {"date_str": "2026-01-01"})]


def test_kz_data_call_falls_back_when_no_session(monkeypatch):
    """When no MCPSessionSync is bound, the call routes through the legacy
    fresh-subprocess path. We assert the routing branch by closing the
    coroutine before asyncio.run sees it (no real subprocess spawned)."""
    sentinel = object()

    def _fake_run(coro):
        coro.close()
        return sentinel

    monkeypatch.setattr("pia.mcp.client.asyncio.run", _fake_run)
    assert active_kz_data_session() is None
    out = kz_data_call_sync("get_nbk_rate")
    assert out is sentinel


def test_bind_and_reset_session_token():
    fake = _FakePooledSession()
    assert active_kz_data_session() is None
    token = bind_kz_data_session(fake)  # type: ignore[arg-type]
    assert active_kz_data_session() is fake
    reset_kz_data_session(token)
    assert active_kz_data_session() is None


def test_session_open_failure_surfaces(monkeypatch):
    """When the subprocess fails to start, ``MCPSessionSync.__enter__`` raises
    so callers (notably ``advise()``) can fall back to the per-call
    subprocess path. We patch the open timeout small to keep the test fast."""
    from mcp.client.stdio import StdioServerParameters

    from pia.mcp.session import MCPSessionSync

    monkeypatch.setattr("pia.mcp.session._OPEN_TIMEOUT_S", 1)
    params = StdioServerParameters(command="/no/such/binary", args=[])
    sess = MCPSessionSync(params)
    with pytest.raises(Exception):  # noqa: B017 — exact type depends on OS
        sess.__enter__()
