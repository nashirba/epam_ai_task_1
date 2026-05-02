# tests/unit/test_planner_disclaimer.py
from unittest.mock import patch

from pia.agents.planner import advise


def test_advise_returns_recommendation_even_when_planner_raises():
    with patch("pia.agents.planner._make_planner") as mp:
        mp.return_value.run.side_effect = RuntimeError("LLM offline")
        rec = advise("anything")
    assert rec.disclaimer  # disclaimer present
    assert "temporarily unavailable" in rec.summary
    assert "RuntimeError" in rec.summary  # type name is surfaced for debugging
