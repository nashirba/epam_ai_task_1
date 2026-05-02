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
    return asyncio.run(kz_data_call(tool_name, **kwargs))


@trace("mcp.web_search")
def web_search_sync(query: str, max_results: int = 5) -> list[dict]:
    return asyncio.run(web_search(query, max_results=max_results))
