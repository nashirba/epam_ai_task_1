# tests/adversarial/test_mcp_timeout.py
import pytest

from pia.agents.planner import advise


@pytest.mark.adversarial
def test_mcp_timeout_degrades_gracefully(monkeypatch, live_llm_required):
    def _boom(tool_name: str, **kwargs):
        raise TimeoutError(f"simulated timeout calling {tool_name}")

    monkeypatch.setattr("pia.mcp.client.kz_data_call_sync", _boom)
    rec = advise("Какая сейчас базовая ставка НБК?")
    # Either the model hedges with a tool-unavailable note, or advise()
    # returns the degraded summary from its outer try/except.
    text = rec.summary.lower()
    assert "temporarily unavailable" in rec.summary or "недоступ" in text or "timeout" in text, (
        rec.summary
    )
    assert rec.disclaimer
