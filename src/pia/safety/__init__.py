"""Safety facade for PIA.

The four public entrypoints and their exception class are re-exported here so
callers only need ``from pia.safety import …``.

Canonical pipeline in ``advise()``:
  rate_limit_check → sanitize_input → redact_pii → planner.run → guardrail_output
"""

from pia.safety.guardrail import guardrail_output
from pia.safety.pii import redact_pii
from pia.safety.ratelimit import RateLimitExceeded, RateLimitExceededError, rate_limit_check
from pia.safety.sanitize import sanitize_input

__all__ = [
    "RateLimitExceeded",
    "RateLimitExceededError",
    "guardrail_output",
    "rate_limit_check",
    "redact_pii",
    "sanitize_input",
]
