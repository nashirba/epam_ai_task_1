# tests/unit/test_planner_citations.py
from unittest.mock import patch, MagicMock

from pia.agents.planner import advise
from pia.agents.base import AgentRunResult
from pia.messages import Citation, PortfolioAnswer, MarketAnswer, MarketSource


def test_advise_propagates_portfolio_citations(monkeypatch):
    fake_portfolio = PortfolioAnswer(
        text="You hold 2500 HSBK at avg 195 KZT.",
        citations=[
            Citation(source="user_holdings", source_url="data/personal/holdings.json", snippet="HSBK 2500 @195"),
            Citation(source="user_note", source_url="data/personal/notes/halyk_thesis.md", snippet="Halyk thesis…"),
        ],
        used_holdings=True,
    )
    fake_market = MarketAnswer(text="HSBK last 215.40 KZT.", sources=[MarketSource(tool="kz-data:get_kase_quote")])

    # We patch _make_planner so we can capture the citation_ledger and market_source_ledger
    # passed to it, then populate them to simulate what the real handlers would do.
    import pia.agents.planner as planner_mod

    original_make_planner = planner_mod._make_planner

    def fake_make_planner(citation_ledger, market_source_ledger):
        # Simulate the portfolio handler populating the ledger
        citation_ledger.extend(fake_portfolio.citations)
        market_source_ledger.extend(fake_market.sources)
        # Return a mock agent whose run() returns a synthetic result
        mock_agent = MagicMock()
        mock_agent.run.return_value = AgentRunResult(
            text="Based on your holdings and the current price, …",
            tool_calls_made=["ask_portfolio", "ask_market"],
            tool_errors=[],
            budget_exhausted=False,
        )
        return mock_agent

    with patch("pia.agents.planner._make_planner", side_effect=fake_make_planner), \
         patch("pia.agents.planner.ask_portfolio", return_value=fake_portfolio), \
         patch("pia.agents.planner.ask_market", return_value=fake_market):
        rec = advise("How is my HSBK position doing?")

    assert rec.citations  # at least one citation reaches the user
    assert any(c.source == "user_note" for c in rec.citations)
    assert rec.disclaimer  # disclaimer always present
