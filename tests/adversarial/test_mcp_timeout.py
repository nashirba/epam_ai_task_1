# tests/adversarial/test_mcp_timeout.py
import pytest

from pia.agents.planner import advise


@pytest.mark.adversarial
def test_mcp_timeout_degrades_gracefully(monkeypatch, live_llm_required):
    def _boom(tool_name: str, **kwargs):
        raise TimeoutError(f"simulated timeout calling {tool_name}")

    monkeypatch.setattr("pia.mcp.client.kz_data_call_sync", _boom)
    rec = advise("Какая сейчас базовая ставка НБК?")
    # Either the model hedges with a "tool unavailable" note, or advise()'s outer try/except returns the degraded summary.
    assert ("temporarily unavailable" in rec.summary or "недоступ" in rec.summary.lower()
            or "timeout" in rec.summary.lower() or rec.market_sources == []), rec.summary
    assert rec.disclaimer
