from __future__ import annotations

from pia.agents.base import BaseAgent, Tool
from pia.agents.market import ask_market
from pia.agents.portfolio import ask_portfolio
from pia.messages import (
    MarketQuery,
    MarketSource,
    PortfolioQuery,
    Recommendation,
)

_SYSTEM = """You are the Planner / Advisor. You combine the user's portfolio
context with current market state to produce evidence-backed recommendations.

Rules:
- ALWAYS call `ask_portfolio` first to ground in what the user owns and their plan.
- Call `ask_market` when current numbers (rates/FX/quotes/news) are needed.
- Do NOT issue definitive buy/sell instructions. Use hedged language: "consider",
  "based on the evidence", and reference your sources.
- Cite the user's plan and current data in every actionable recommendation.
- Output should be concise: 2-4 short sections at most.
"""


def make_planner() -> BaseAgent:
    return BaseAgent(
        name="planner",
        system_prompt=_SYSTEM,
        tools=[
            Tool(
                name="ask_portfolio",
                description="Ask the Portfolio Agent about the user's holdings/plan/notes.",
                parameters={
                    "type": "object",
                    "properties": {"question": {"type": "string"}},
                    "required": ["question"],
                },
                handler=lambda question: ask_portfolio(
                    PortfolioQuery(question=question)
                ).model_dump(),
            ),
            Tool(
                name="ask_market",
                description="Ask the Market Agent about current rates/FX/KASE/deposits/news.",
                parameters={
                    "type": "object",
                    "properties": {"question": {"type": "string"}},
                    "required": ["question"],
                },
                handler=lambda question: ask_market(MarketQuery(question=question)).model_dump(),
            ),
        ],
    )


def advise(user_text: str) -> Recommendation:
    planner = make_planner()
    summary = planner.run(user_text)
    # Light post-processing: hedge language enforcement (best-effort guardrail)
    hedge_triggers = [" buy ", " sell ", "recommend buying", "recommend selling"]
    if any(p in summary.lower() for p in hedge_triggers):
        summary = "Hedged note: " + summary
    return Recommendation(
        summary=summary,
        actions=[],
        citations=[],
        market_sources=[MarketSource(tool="planner")],
    )
