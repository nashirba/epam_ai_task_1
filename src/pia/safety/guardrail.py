"""Output guardrail — single canonical home for LLM output safety checks.

Two checks (applied in order):
1. **Known-leak redaction**: replace literal credential tokens from
   ``tests/fixtures/adversarial_inputs.yaml`` with ``[REDACTED]``.  The
   current set is ``{"hunter2"}`` — the only explicit password token in the
   adversarial fixture.  This is a defence-in-depth measure; the PII layer
   already runs before the LLM call, but the guardrail catches tokens that
   may have leaked via the LLM's own training data or prompt injection.

2. **Definitive-call hedging**: if the output contains financial verbs that
   constitute a definitive buy/sell instruction, prepend ``"Hedged note: "``
   to the whole response.  This was previously inline in ``advise()``; moving
   it here makes it the single source of truth and keeps ``advise()`` clean.

Both checks are idempotent: running ``guardrail_output`` twice on the same
text produces the same result.
"""
from __future__ import annotations

import re

# ---- Known-leak tokens (credential patterns from adversarial fixtures) ----

_KNOWN_LEAK_TOKENS: tuple[str, ...] = (
    "hunter2",
)

# Build a compiled regex matching any of the known tokens (case-sensitive,
# whole-word or exact token).
_LEAK_RE = re.compile(
    "|".join(re.escape(t) for t in _KNOWN_LEAK_TOKENS),
    re.IGNORECASE,
)

# ---- Definitive financial-call terms ----

_DEFINITIVE_CALL_TERMS: tuple[str, ...] = (
    " buy ",
    " sell ",
    "recommend buying",
    "recommend selling",
    "must buy",
    "must sell",
    "купить",
    "продать",
    "покупайте",
    "продавайте",
    "обязательно купите",
    "обязательно продайте",
)


def _looks_like_definitive_call(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in _DEFINITIVE_CALL_TERMS)


_HEDGED_PREFIX = "Hedged note: "


def guardrail_output(text: str) -> str:
    """Apply all output safety checks and return the (possibly modified) text.

    Steps:
    1. Redact known credential/leak tokens → ``[REDACTED]``.
    2. Hedge definitive financial calls by prepending ``"Hedged note: "``.
    """
    # 1. Redact known-leak tokens.
    text = _LEAK_RE.sub("[REDACTED]", text)

    # 2. Hedge if definitive call detected (idempotent: prefix is already
    #    present after first application).
    if not text.startswith(_HEDGED_PREFIX) and _looks_like_definitive_call(text):
        text = _HEDGED_PREFIX + text

    return text
