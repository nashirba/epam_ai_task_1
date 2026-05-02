# tests/unit/test_planner_citations.py
from unittest.mock import MagicMock

import pia.agents.planner as planner_mod
from pia.agents.planner import advise
from pia.messages import Citation, MarketAnswer, MarketSource, PortfolioAnswer


def test_advise_propagates_portfolio_citations(monkeypatch):
    fake_portfolio = PortfolioAnswer(
        text="You hold 2500 HSBK at avg 195 KZT.",
        citations=[
            Citation(
                source="user_holdings",
                source_url="data/personal/holdings.json",
                snippet="HSBK 2500 @195",
            ),
            Citation(
                source="user_note",
                source_url="data/personal/notes/halyk_thesis.md",
                snippet="Halyk thesis…",
            ),
        ],
        used_holdings=True,
    )
    fake_market = MarketAnswer(
        text="HSBK last 215.40 KZT.",
        sources=[MarketSource(tool="kz-data:get_kase_quote")],
    )

    monkeypatch.setattr(planner_mod, "ask_portfolio", lambda _q: fake_portfolio)
    monkeypatch.setattr(planner_mod, "ask_market", lambda _q: fake_market)

    # Script the LLM: tool-call ask_portfolio, tool-call ask_market, then final answer.
    fake_llm = MagicMock()
    fake_llm.chat.side_effect = [
        {
            "content": "",
            "tool_calls": [
                {
                    "id": "1",
                    "function": {
                        "name": "ask_portfolio",
                        "arguments": '{"question": "HSBK position?"}',
                    },
                },
            ],
        },
        {
            "content": "",
            "tool_calls": [
                {
                    "id": "2",
                    "function": {
                        "name": "ask_market",
                        "arguments": '{"question": "HSBK quote?"}',
                    },
                },
            ],
        },
        {
            "content": "Based on your holdings and the current price, your HSBK position is up.",
            "tool_calls": [],
        },
    ]

    # Inject the fake LLM into every BaseAgent constructed by the planner module.
    real_base_agent = planner_mod.BaseAgent

    def base_agent_with_fake_llm(*args, **kwargs):
        kwargs.setdefault("llm", fake_llm)
        return real_base_agent(*args, **kwargs)

    monkeypatch.setattr(planner_mod, "BaseAgent", base_agent_with_fake_llm)

    rec = advise("How is my HSBK position doing?")

    assert rec.citations, "no citations propagated to Recommendation"
    assert any(c.source == "user_note" for c in rec.citations)
    assert any(c.source == "user_holdings" for c in rec.citations)
    assert rec.market_sources, "no market_sources propagated to Recommendation"
    assert any(s.tool == "kz-data:get_kase_quote" for s in rec.market_sources)
    assert rec.disclaimer
