"""Token-bucket rate limiter — process-local, 10 requests / 60 seconds default.

Design notes
------------
- The bucket is **process-local**: it does not persist across Streamlit
  hot-reloads or pytest sessions.  This is acceptable for a capstone demo
  (documented in ADR-0011).
- ``PIA_RATE_LIMIT_PER_MINUTE`` env-var (integer) overrides the setting read
  from ``pia.config``.  Set it to a large value (e.g. ``99999``) to effectively
  disable rate-limiting in tests.
- ``_reset()`` re-fills the bucket to capacity and resets the window start;
  used by ``tests/unit/test_ratelimit.py`` and by the conftest autouse fixture
  that prevents bucket exhaustion across test functions.
"""

from __future__ import annotations

import os
import time

from pia.config import get_settings as _get_settings


def _read_limit() -> int:
    env_override = os.getenv("PIA_RATE_LIMIT_PER_MINUTE")
    if env_override is not None:
        return int(env_override)
    return _get_settings().rate_limit_per_minute


class RateLimitExceededError(Exception):
    """Raised when the token bucket is exhausted."""


RateLimitExceeded = RateLimitExceededError


# ---------- module-level bucket state ----------

_CAPACITY: int = _read_limit()
_WINDOW_SECONDS: float = 60.0

_tokens: float = float(_CAPACITY)
_window_start: float = time.monotonic()


def _reset() -> None:
    """Refill bucket to full capacity and restart the window.

    Intended for test isolation; call before each test that exercises the
    rate limiter.
    """
    global _tokens, _window_start, _CAPACITY
    _CAPACITY = _read_limit()
    _tokens = float(_CAPACITY)
    _window_start = time.monotonic()


def rate_limit_check() -> None:
    """Consume one token from the bucket or raise ``RateLimitExceededError``.

    Refills the bucket proportionally when the elapsed time since the last
    refill exceeds the window.  The standard leaky-bucket approach: tokens
    accumulate at ``capacity / window_seconds`` per second, capped at capacity.
    """
    global _tokens, _window_start

    now = time.monotonic()
    elapsed = now - _window_start

    # Refill: add tokens proportional to elapsed time, capped at capacity.
    if elapsed > 0:
        refill = elapsed * (_CAPACITY / _WINDOW_SECONDS)
        _tokens = min(float(_CAPACITY), _tokens + refill)
        _window_start = now

    if _tokens < 1.0:
        raise RateLimitExceededError(
            f"Rate limit of {_CAPACITY} requests/minute exceeded. Please wait and try again."
        )
    _tokens -= 1.0
