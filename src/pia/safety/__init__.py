"""Safety facade for PIA.

The four public entrypoints and their exception class are re-exported here so
callers only need ``from pia.safety import …``.

Canonical pipeline in ``advise()``:
  sanitize_input → redact_pii → rate_limit_check → planner.run → guardrail_output
"""
from pia.safety.guardrail import guardrail_output
from pia.safety.pii import redact_pii
from pia.safety.ratelimit import RateLimitExceeded, rate_limit_check
from pia.safety.sanitize import sanitize_input

__all__ = [
    "sanitize_input",
    "redact_pii",
    "rate_limit_check",
    "guardrail_output",
    "RateLimitExceeded",
]
