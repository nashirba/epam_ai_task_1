from __future__ import annotations

import asyncio
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from pia.config import get_settings
from pia.observability import trace
from pia.observability.metrics import record_call


@asynccontextmanager
async def _stdio(params: StdioServerParameters) -> AsyncIterator[ClientSession]:
    async with stdio_client(params) as (r, w), ClientSession(r, w) as session:
        await session.initialize()
        yield session


async def kz_data_call(tool_name: str, **kwargs: Any) -> Any:
    settings = get_settings()
    params = StdioServerParameters(
        command=sys.executable,
        args=[settings.kz_data_mcp_path],
    )
    async with _stdio(params) as session:
        result = await session.call_tool(tool_name, arguments=kwargs)
        return result.content[0].text if result.content else None


async def web_search(query: str, max_results: int = 5) -> list[dict]:
    """Tavily MCP. Falls back to a no-op if TAVILY_API_KEY is missing."""
    tavily_api_key = get_settings().tavily_api_key
    if not tavily_api_key:
        return []
    params = StdioServerParameters(
        command="npx",
        args=["-y", "@tavily/mcp"],
        env={**os.environ, "TAVILY_API_KEY": tavily_api_key},
    )
    async with _stdio(params) as session:
        result = await session.call_tool(
            "tavily_search", arguments={"query": query, "max_results": max_results}
        )
        return [{"text": result.content[0].text}] if result.content else []


@trace("mcp.kz_data")
def kz_data_call_sync(tool_name: str, **kwargs: Any) -> Any:
    """Sync entrypoint for kz-data tool calls.

    When a per-request :class:`MCPSessionSync` is bound (see
    :mod:`pia.mcp.session`), the call is dispatched through it so subprocess
    startup is paid once per ``advise()`` call rather than once per tool call.
    Otherwise we fall back to a fresh subprocess so this function still works
    standalone in unit tests and ad-hoc CLI use.
    """
    from pia.mcp.session import active_kz_data_session

    with record_call("mcp.kz_data"):
        pooled = active_kz_data_session()
        if pooled is not None:
            return pooled.call(tool_name, **kwargs)
        return asyncio.run(kz_data_call(tool_name, **kwargs))


@trace("mcp.web_search")
def web_search_sync(query: str, max_results: int = 5) -> list[dict]:
    with record_call("mcp.web_search"):
        return asyncio.run(web_search(query, max_results=max_results))
