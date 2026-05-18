# tests/unit/test_planner_disclaimer.py
from unittest.mock import patch

import litellm

from pia.agents.planner import advise


def test_advise_returns_recommendation_even_when_planner_raises():
    with patch("pia.agents.planner._make_planner") as mp:
        mp.return_value.run.side_effect = RuntimeError("LLM offline")
        rec = advise("anything")
    assert rec.disclaimer  # disclaimer present
    assert "temporarily unavailable" in rec.summary
    assert "RuntimeError" in rec.summary  # type name is surfaced for debugging


def test_advise_returns_rate_limit_message_when_provider_throttles():
    err = litellm.RateLimitError(
        message="429 Too Many Requests", model="gemini/x", llm_provider="gemini"
    )
    with patch("pia.agents.planner._make_planner") as mp:
        mp.return_value.run.side_effect = err
        rec = advise("anything")
    assert "rate-limiting" in rec.summary
    assert rec.disclaimer
