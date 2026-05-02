# tests/unit/test_pii.py
"""Unit tests for pia.safety.pii.redact_pii."""
import pytest

from pia.safety.pii import redact_pii


# ---- IIN tests ----

def test_iin_redacted():
    assert redact_pii("My IIN is 123456789012") == "My IIN is [IIN]"


def test_iin_not_partial_match():
    # 13-digit number should NOT be redacted as IIN
    result = redact_pii("Number 1234567890123 is not an IIN")
    assert "[IIN]" not in result
    assert "1234567890123" in result


def test_iin_word_boundary_false_positive_is_documented_behavior():
    """Per ADR-0011: 12-digit standalone numbers are unconditionally redacted as IIN,
    including legitimate-looking serial or tracking IDs. This is an accepted false
    positive in the regex baseline. If the regex is later tightened to require IIN
    context, update both this test and ADR-0011."""
    assert redact_pii("Serial: 123456789012") == "Serial: [IIN]"
    assert redact_pii("Tracking number 999888777666") == "Tracking number [IIN]"


def test_standalone_12_digit_number_redacted():
    # Conservative: bare 12-digit standalone number is redacted (acceptable FP).
    result = redact_pii("Account 123456789012 is new")
    assert "[IIN]" in result


# ---- Phone tests ----

def test_phone_plus7_redacted():
    assert redact_pii("My phone is +77011234567") == "My phone is [PHONE]"


def test_phone_8_prefix_redacted():
    assert redact_pii("Call me at 87771234567") == "Call me at [PHONE]"


def test_phone_with_spaces_redacted():
    result = redact_pii("Phone: +7 701 123 45 67")
    assert "[PHONE]" in result
    assert "+7 701 123 45 67" not in result


def test_phone_does_not_eat_iin():
    # A 12-digit IIN should be caught by IIN, not misidentified as phone.
    # Phone regex requires +7 or 8 prefix so "123456789012" should be IIN.
    result = redact_pii("123456789012")
    assert "[IIN]" in result
    assert "[PHONE]" not in result


# ---- IBAN tests ----

def test_iban_redacted():
    assert redact_pii("IBAN: KZ751900007999999999") == "IBAN: [IBAN]"


def test_iban_only_kz_prefix():
    # Non-KZ IBANs (e.g. DE) should not be redacted.
    result = redact_pii("DE89370400440532013000")
    assert "[IBAN]" not in result


# ---- Email tests ----

def test_email_redacted():
    result = redact_pii("Email me at user@example.com")
    assert "[EMAIL]" in result
    assert "user" not in result


def test_email_in_sentence():
    result = redact_pii("Contact admin@pia.kz for help")
    assert "[EMAIL]" in result
    assert "admin" not in result


def test_email_not_false_positive_on_plain_text():
    result = redact_pii("Just a normal sentence with no PII.")
    assert result == "Just a normal sentence with no PII."


# ---- Multiple PII in one string ----

def test_multiple_pii_types():
    text = "IIN 123456789012, email user@test.com, phone +77011234567"
    result = redact_pii(text)
    assert "[IIN]" in result
    assert "[EMAIL]" in result
    assert "[PHONE]" in result
    assert "123456789012" not in result
    assert "user@test.com" not in result
    assert "+77011234567" not in result


# ---- No PII — text unchanged ----

def test_no_pii_unchanged():
    text = "What is the NBK base rate today?"
    assert redact_pii(text) == text
