# tests/unit/test_sanitize.py
"""Unit tests for pia.safety.sanitize.sanitize_input."""
import pytest

from pia.safety.sanitize import sanitize_input


def test_strips_null_bytes():
    assert sanitize_input("\x00hello") == "hello"


def test_strips_control_chars_preserves_newline_and_tab():
    result = sanitize_input("\x00 hi\n\there\x1f")
    assert "\x00" not in result
    assert "\x1f" not in result
    assert "\n" in result
    assert "\t" in result
    assert "hi" in result
    assert "here" in result


def test_strips_del_char():
    assert sanitize_input("abc\x7fdef") == "abcdef"


def test_trims_whitespace():
    assert sanitize_input("  hello world  ") == "hello world"


def test_unicode_normalization_nfkc():
    # NFKC: fullwidth digit should become ASCII digit
    assert sanitize_input("０") == "0"


def test_caps_at_8000_chars():
    long_text = "a" * 10_000
    result = sanitize_input(long_text)
    assert len(result) == 8_000


def test_empty_string():
    assert sanitize_input("") == ""


def test_only_whitespace():
    assert sanitize_input("   \t  \n  ") == ""


def test_normal_text_unchanged():
    text = "What is the NBK rate today?"
    assert sanitize_input(text) == text


def test_preserves_unicode_letters():
    text = "Сколько стоит доллар сегодня?"
    assert sanitize_input(text) == text
