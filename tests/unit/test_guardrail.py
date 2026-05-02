# tests/unit/test_guardrail.py
"""Unit tests for pia.safety.guardrail.guardrail_output."""
import pytest

from pia.safety.guardrail import guardrail_output


# ---- Definitive-call hedging ----

def test_hedges_buy_instruction():
    result = guardrail_output("You should buy HSBK shares today.")
    assert result.startswith("Hedged note:")


def test_hedges_sell_instruction():
    result = guardrail_output("You must sell KZTO immediately.")
    assert result.startswith("Hedged note:")


def test_hedges_recommend_buying():
    result = guardrail_output("I recommend buying more bonds.")
    assert result.startswith("Hedged note:")


def test_hedges_russian_купить():
    result = guardrail_output("Следует купить акции.")
    assert result.startswith("Hedged note:")


def test_hedges_russian_продать():
    result = guardrail_output("Вы должны продать всё.")
    assert result.startswith("Hedged note:")


def test_no_hedge_on_normal_text():
    result = guardrail_output("Consider diversifying your portfolio.")
    assert not result.startswith("Hedged note:")


def test_hedge_is_idempotent():
    """Applying guardrail twice produces the same result as once."""
    text = "You should buy HSBK."
    once = guardrail_output(text)
    twice = guardrail_output(once)
    assert once == twice
    assert once.count("Hedged note:") == 1


# ---- Known-leak redaction ----

def test_hunter2_redacted():
    result = guardrail_output("Halyk thesis with hunter2 password")
    assert "hunter2" not in result
    assert "[REDACTED]" in result


def test_hunter2_case_insensitive():
    result = guardrail_output("The password is HUNTER2 here.")
    assert "HUNTER2" not in result
    assert "[REDACTED]" in result


def test_no_redaction_on_clean_text():
    text = "Based on the evidence, consider rebalancing."
    assert guardrail_output(text) == text


def test_leak_redaction_and_hedge_combined():
    """Both redaction and hedging apply in the same pass."""
    text = "You should buy HSBK (password: hunter2)"
    result = guardrail_output(text)
    assert "hunter2" not in result
    assert "[REDACTED]" in result
    assert result.startswith("Hedged note:")
