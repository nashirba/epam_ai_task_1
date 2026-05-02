# tests/unit/test_ratelimit.py
"""Unit tests for pia.safety.ratelimit — token bucket rate limiter."""

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


def test_bucket_refills_over_time(monkeypatch):
    """After the window partially elapses, capacity refills proportionally.

    With capacity=6 and window=60s the refill rate is 6/60 = 0.1 tokens/sec.
    After 30 seconds of elapsed time the bucket should gain exactly 3 tokens
    (30 * 0.1 = 3.0), allowing 3 more calls before the bucket empties again.

    The mock supplies time.monotonic() values in call order:
      index 0   — _reset() sets _window_start
      index 1-7 — the 7 rate_limit_check() calls in the first block
      index 8-11 — the 4 rate_limit_check() calls in the second block
    """
    from unittest.mock import patch

    monkeypatch.setenv("PIA_RATE_LIMIT_PER_MINUTE", "6")
    from pia.safety import ratelimit

    # _CAPACITY must be re-read from the env var
    ratelimit._reset()  # this consumes the first monotonic() call from the iterator

    # Sequence: 1 for _reset, 7 for first block, 4 for second block = 12 total
    times = iter(
        [
            0.0,  # _reset() → _window_start = 0
            0.0,  # call 1 — elapsed=0, tokens: 6→5
            0.0,  # call 2 — tokens: 5→4
            0.0,  # call 3 — tokens: 4→3
            0.0,  # call 4 — tokens: 3→2
            0.0,  # call 5 — tokens: 2→1
            0.0,  # call 6 — tokens: 1→0
            0.0,  # call 7 — elapsed=0, tokens=0 < 1 → RateLimitExceeded
            30.0,  # call 8 — elapsed=30, refill=3.0, tokens: 0+3=3→2
            30.0,  # call 9 — elapsed=0, tokens: 2→1
            30.0,  # call 10 — tokens: 1→0
            30.0,  # call 11 — elapsed=0, tokens=0 < 1 → RateLimitExceeded
        ]
    )

    with patch("pia.safety.ratelimit.time.monotonic", lambda: next(times)):
        ratelimit._reset()  # sets _window_start=0.0; consumes index 0

        # Exhaust the 6-token bucket
        for _ in range(6):
            ratelimit.rate_limit_check()  # consumes indices 1-6

        with pytest.raises(ratelimit.RateLimitExceeded):
            ratelimit.rate_limit_check()  # consumes index 7 — bucket empty

        # Advance to t=30: 3 tokens should have been refilled
        for _ in range(3):
            ratelimit.rate_limit_check()  # consumes indices 8-10

        with pytest.raises(ratelimit.RateLimitExceeded):
            ratelimit.rate_limit_check()  # consumes index 11 — bucket empty again
