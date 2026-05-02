# tests/unit/test_ratelimit.py
"""Unit tests for pia.safety.ratelimit — token bucket rate limiter."""
import os
import time

import pytest

from pia.safety.ratelimit import RateLimitExceeded, _reset, rate_limit_check


def test_first_call_succeeds():
    """A freshly-reset bucket allows the first call."""
    _reset()
    rate_limit_check()  # should not raise


def test_calls_up_to_capacity_succeed(monkeypatch):
    """Calls up to the capacity limit all succeed."""
    monkeypatch.setenv("PIA_RATE_LIMIT_PER_MINUTE", "5")
    _reset()
    for _ in range(5):
        rate_limit_check()  # all 5 should pass


def test_exceeding_capacity_raises(monkeypatch):
    """The (N+1)th call within the window raises RateLimitExceeded."""
    monkeypatch.setenv("PIA_RATE_LIMIT_PER_MINUTE", "3")
    _reset()
    for _ in range(3):
        rate_limit_check()
    with pytest.raises(RateLimitExceeded):
        rate_limit_check()


def test_rate_limit_exceeded_is_exception():
    assert issubclass(RateLimitExceeded, Exception)


def test_reset_refills_bucket(monkeypatch):
    """After exhausting the bucket, _reset() allows calls again."""
    monkeypatch.setenv("PIA_RATE_LIMIT_PER_MINUTE", "2")
    _reset()
    rate_limit_check()
    rate_limit_check()
    with pytest.raises(RateLimitExceeded):
        rate_limit_check()
    _reset()
    rate_limit_check()  # should succeed after reset


def test_env_var_override_high_limit(monkeypatch):
    """Setting PIA_RATE_LIMIT_PER_MINUTE to a high value disables the limit."""
    monkeypatch.setenv("PIA_RATE_LIMIT_PER_MINUTE", "10000")
    _reset()
    for _ in range(100):
        rate_limit_check()  # far below 10000; all should pass
