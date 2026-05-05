from __future__ import annotations

import contextlib
from uuid import uuid4

from pia.agents.base import BaseAgent, Tool
from pia.agents.market import ask_market
from pia.agents.portfolio import ask_portfolio
from pia.mcp.session import (
    MCPSessionSync,
    bind_kz_data_session,
    kz_data_params,
    reset_kz_data_session,
)
from pia.messages import (
    AgentMessage,
    Citation,
    MarketQuery,
    MarketSource,
    PortfolioQuery,
    Recommendation,
)
from pia.observability import reset_request_id, set_request_id, trace
from pia.observability.metrics import get_registry, record_call
from pia.safety import (
    RateLimitExceeded,
    guardrail_output,
    rate_limit_check,
    redact_pii,
    sanitize_input,
)

_SYSTEM = """You are the Planner / Advisor. You combine the user's portfolio context
with current market state to produce evidence-backed recommendations.

Rules:
- ALWAYS call `ask_portfolio` first to ground in what the user owns and their plan.
- Call `ask_market` when current numbers (rates/FX/quotes/news) are needed.
- Do NOT issue definitive buy/sell instructions. Use hedged language: "consider",
  "based on the evidence", and reference your sources.
- Cite the user's plan and current data in every actionable recommendation.
- Output should be concise: 2-4 short sections at most.
"""


def _make_planner(
    citation_ledger: list[Citation],
    market_source_ledger: list[MarketSource],
) -> BaseAgent:
    def _portfolio_handler(question: str) -> dict:
        request = AgentMessage(
            sender="planner",
            receiver="portfolio",
            payload=PortfolioQuery(question=question),
        )
        answer = ask_portfolio(request.payload)
        citation_ledger.extend(answer.citations)
        return AgentMessage(
            sender="portfolio",
            receiver="planner",
            payload=answer,
        ).payload.model_dump()

    def _market_handler(question: str) -> dict:
        request = AgentMessage(
            sender="planner",
            receiver="market",
            payload=MarketQuery(question=question),
        )
        answer = ask_market(request.payload)
        market_source_ledger.extend(answer.sources)
        return AgentMessage(
            sender="market",
            receiver="planner",
            payload=answer,
        ).payload.model_dump()

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
                    "additionalProperties": False,
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
                    "additionalProperties": False,
                },
                handler=_market_handler,
            ),
        ],
    )


def make_planner() -> BaseAgent:  # backward-compatible factory used by tests/UI
    return _make_planner([], [])


def advise(user_text: str) -> Recommendation:
    """Public entrypoint. Binds a per-call request id so every nested Langfuse
    observation rolls up under one trace, opens one pooled kz-data MCP
    session for the duration of the call, then runs the safety facade.

    The kz-data subprocess pool is best-effort — if the subprocess fails to
    spawn (Weaviate down, FastMCP missing, OS hand-off), we fall through to
    the per-call subprocess path inside ``kz_data_call_sync`` instead of
    failing the whole request.
    """
    request_id = uuid4().hex
    rid_token = set_request_id(request_id)
    get_registry().set_last_request_id(request_id)
    session: MCPSessionSync | None = None
    session_token = None
    try:
        try:
            session = MCPSessionSync(kz_data_params())
            session.__enter__()
        except Exception:  # noqa: BLE001 — pool open is best-effort; fall back to per-call subprocess
            session = None
        if session is not None:
            session_token = bind_kz_data_session(session)
        with record_call("advise"):
            return _advise_inner(user_text)
    finally:
        if session_token is not None:
            reset_kz_data_session(session_token)
        if session is not None:
            with contextlib.suppress(Exception):  # best-effort cleanup
                session.__exit__(None, None, None)
        reset_request_id(rid_token)


@trace("agent.planner.advise")
def _advise_inner(user_text: str) -> Recommendation:
    try:
        rate_limit_check()
    except RateLimitExceeded:
        return Recommendation(
            summary="Rate limit exceeded. Please wait a minute and try again.",
            actions=[],
            citations=[],
            market_sources=[],
        )
    user_text = redact_pii(sanitize_input(user_text))
    citations: list[Citation] = []
    market_sources: list[MarketSource] = []
    planner = _make_planner(citations, market_sources)
    try:
        result = planner.run(user_text)
        summary = result.text
    except Exception as exc:  # noqa: BLE001 — degraded answer path; disclaimer must always reach the user
        summary = (
            f"The advisor is temporarily unavailable ({type(exc).__name__}). "
            "Please try again in a moment."
        )
    summary = guardrail_output(summary)
    return Recommendation(
        summary=summary,
        actions=[],
        citations=citations[:8],  # cap to keep UI tidy
        market_sources=market_sources[:6],
    )
