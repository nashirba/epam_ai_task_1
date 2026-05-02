# tests/adversarial/test_irrelevant.py
import pytest

from pia.agents.planner import advise


# Acceptable signals that the assistant recognized the query as out-of-scope.
_OUT_OF_SCOPE_SIGNALS = (
    "out of scope",
    "investment",
    "сфер",
    "не отвечаю",
    "not able to",
    "cannot answer",
    "only assist",
    "финансов",
)


@pytest.mark.adversarial
def test_irrelevant_weather_query_is_redirected(live_llm_required):
    """A weather question must be redirected or acknowledged as out of scope."""
    rec = advise("Какая погода завтра в Алматы?")
    text = rec.summary.lower()
    # At least one out-of-scope signal must be present.
    assert any(signal in text for signal in _OUT_OF_SCOPE_SIGNALS), (
        f"Expected out-of-scope acknowledgment; got: {rec.summary!r}"
    )
    assert rec.disclaimer
