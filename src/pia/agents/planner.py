from __future__ import annotations

from pia.agents.base import BaseAgent, Tool
from pia.agents.market import ask_market
from pia.agents.portfolio import ask_portfolio
from pia.messages import (
    AgentMessage,
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


_DEFINITIVE_CALL_TERMS = (
    " buy ",
    " sell ",
    "recommend buying",
    "recommend selling",
    "must buy",
    "must sell",
    "купить",  # imperative or infinitive
    "продать",
    "покупайте",
    "продавайте",
    "обязательно купите",
    "обязательно продайте",
)


def _looks_like_definitive_call(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in _DEFINITIVE_CALL_TERMS)


def _portfolio_handler(question: str) -> dict:
    request = AgentMessage(
        sender="planner",
        receiver="portfolio",
        payload=PortfolioQuery(question=question),
    )
    answer = ask_portfolio(request.payload)  # type: ignore[arg-type]
    response = AgentMessage(
        sender="portfolio",
        receiver="planner",
        payload=answer,
    )
    return response.payload.model_dump()


def _market_handler(question: str) -> dict:
    request = AgentMessage(
        sender="planner",
        receiver="market",
        payload=MarketQuery(question=question),
    )
    answer = ask_market(request.payload)  # type: ignore[arg-type]
    response = AgentMessage(
        sender="market",
        receiver="planner",
        payload=answer,
    )
    return response.payload.model_dump()


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
                handler=_portfolio_handler,
            ),
            Tool(
                name="ask_market",
                description="Ask the Market Agent about current rates/FX/KASE/deposits/news.",
                parameters={
                    "type": "object",
                    "properties": {"question": {"type": "string"}},
                    "required": ["question"],
                },
                handler=_market_handler,
            ),
        ],
    )


def advise(user_text: str) -> Recommendation:
    planner = make_planner()
    try:
        result = planner.run(user_text)
        summary = result.text
    except Exception as exc:  # noqa: BLE001 — degraded answer path; disclaimer must always reach the user
        summary = (
            f"The advisor is temporarily unavailable ({type(exc).__name__}). "
            "Please try again in a moment."
        )
    if _looks_like_definitive_call(summary):
        summary = "Hedged note: " + summary
    return Recommendation(
        summary=summary,
        actions=[],
        citations=[],
        market_sources=[MarketSource(tool="planner")],
    )
