from __future__ import annotations

import json
from pathlib import Path

from pia.agents.base import BaseAgent, Tool
from pia.config import get_settings
from pia.messages import Citation, PortfolioAnswer, PortfolioQuery
from pia.rag.retrieve import retrieve

_SYSTEM = """You are the Portfolio Agent. You answer questions about the user's
holdings, plan, and personal notes.

Rules:
- Use the `retrieve` tool to find the user's notes/plan/holdings before answering.
- Use the `get_holdings` tool to read structured holdings JSON.
- If you cannot find evidence in the user's data, say "I don't have that
  information." — never guess.
- Always return citations.
"""


def _retrieve_tool(query: str, source: str | None = None, k: int = 5) -> list[dict]:
    chunks = retrieve(query, k=k, source=source)
    return [
        {
            "text": c.text,
            "source": c.source,
            "source_url": c.source_url,
            "score": c.score,
            "language": c.language,
        }
        for c in chunks
    ]


def _get_holdings() -> dict:
    p = Path(get_settings().data_dir) / "personal/holdings.json"
    return json.loads(p.read_text())


def make_portfolio_agent() -> BaseAgent:
    return BaseAgent(
        name="portfolio",
        system_prompt=_SYSTEM,
        tools=[
            Tool(
                name="retrieve",
                description="Search the user's notes/plan/holdings/news/etc. for context.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "source": {
                            "type": "string",
                            "enum": [
                                "user_note",
                                "user_plan",
                                "user_holdings",
                                "news",
                                "bank_rates",
                                "kase",
                                "nbk",
                                "real_estate",
                            ],
                        },
                        "k": {"type": "integer", "default": 5},
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
                handler=_retrieve_tool,
            ),
            Tool(
                name="get_holdings",
                description="Return the user's structured holdings JSON.",
                parameters={"type": "object", "properties": {}, "additionalProperties": False},
                handler=_get_holdings,
            ),
        ],
    )


def ask_portfolio(query: PortfolioQuery) -> PortfolioAnswer:
    agent = make_portfolio_agent()
    result = agent.run(query.question)
    cites: list[Citation] = []
    if "retrieve" in result.tool_calls_made:
        # Re-pull citations for the UI; the loop already retrieved them but we
        # don't surface those raw chunks back through the LLM tool channel.
        chunks = retrieve(query.question, k=5)
        cites = [
            Citation(
                source=c.source,
                source_url=c.source_url,
                published_at=c.published_at,
                snippet=c.text[:200],
                score=c.score,
            )
            for c in chunks[:3]
        ]
    return PortfolioAnswer(
        text=result.text,
        citations=cites,
        used_holdings="get_holdings" in result.tool_calls_made,
    )
