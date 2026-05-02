from __future__ import annotations

from pia.agents.base import BaseAgent, Tool
from pia.mcp.client import kz_data_call_sync, web_search_sync
from pia.messages import MarketAnswer, MarketQuery, MarketSource
from pia.observability import trace

_SYSTEM = """You are the Market Agent. You answer questions about current market state for KZ:
NBK rate, FX, KASE quotes, bank deposit rates, and breaking news.

Rules:
- Always call a tool before stating a number — do not invent.
- Surface the `last_updated`/`as_of` field from tools so the user knows staleness.
- If a tool fails, say so plainly and continue with what you have.
"""


def make_market_agent() -> BaseAgent:
    return BaseAgent(
        name="market",
        system_prompt=_SYSTEM,
        tools=[
            Tool(
                "get_nbk_rate",
                "NBK base rate at a date or latest.",
                {
                    "type": "object",
                    "properties": {"date_str": {"type": "string"}},
                    "additionalProperties": False,
                },
                handler=lambda **kw: kz_data_call_sync("get_nbk_rate", **kw),
            ),
            Tool(
                "get_fx_rate",
                "FX spot or historical for KZT/USD, KZT/EUR, KZT/RUB.",
                {
                    "type": "object",
                    "properties": {
                        "pair": {"type": "string"},
                        "date_str": {"type": "string"},
                    },
                    "required": ["pair"],
                    "additionalProperties": False,
                },
                handler=lambda **kw: kz_data_call_sync("get_fx_rate", **kw),
            ),
            Tool(
                "get_kase_quote",
                "Latest KASE snapshot for a ticker.",
                {
                    "type": "object",
                    "properties": {"ticker": {"type": "string"}},
                    "required": ["ticker"],
                    "additionalProperties": False,
                },
                handler=lambda **kw: kz_data_call_sync("get_kase_quote", **kw),
            ),
            Tool(
                "get_deposit_rates",
                "Bank deposit rates across banks for a currency and term.",
                {
                    "type": "object",
                    "properties": {
                        "currency": {"type": "string"},
                        "term_months": {"type": "integer"},
                    },
                    "required": ["currency", "term_months"],
                    "additionalProperties": False,
                },
                handler=lambda **kw: kz_data_call_sync("get_deposit_rates", **kw),
            ),
            Tool(
                "web_search",
                "Public web search for breaking news and external context.",
                {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "max_results": {"type": "integer", "default": 5},
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
                handler=lambda **kw: web_search_sync(**kw),
            ),
        ],
    )


@trace("agent.market")
def ask_market(query: MarketQuery) -> MarketAnswer:
    agent = make_market_agent()
    result = agent.run(query.question)
    sources: list[MarketSource] = []
    seen: set[str] = set()
    for name in result.tool_calls_made:
        if name in seen:
            continue
        seen.add(name)
        if name == "web_search":
            sources.append(MarketSource(tool="tavily-web-search"))
        else:
            sources.append(MarketSource(tool=f"kz-data:{name}"))
    return MarketAnswer(
        text=result.text,
        sources=sources,
        degraded=bool(result.tool_errors) or result.budget_exhausted,
    )
