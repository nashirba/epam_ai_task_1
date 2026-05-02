# ADR 0011: Safety — Layered Facade in `advise()`

- **Status:** Accepted
- **Date:** 2026-05-02
- **Deciders:** Project owner (Nurlan), AI pair

## Context

The capstone grading rubric awards points for safety / guardrails.  Prior
phases had a single inline check in ``advise()`` (the ``_looks_like_definitive_call``
hedge), but no input sanitisation, PII protection, or rate limiting.  The
post-draft plan (Phase 9) requires a proper safety facade.

Requirements:
- Strip malformed input before it reaches the LLM.
- Prevent user PII from being forwarded to the LLM in plaintext.
- Prevent trivial DoS / API-cost abuse via request bursting.
- Ensure LLM output never contains definitive financial instructions or
  credential tokens that leaked through prompt injection.
- Keep the implementation testable in a $0 / no-credentials environment.

## Decision

A **layered facade** wraps the core planner call inside ``advise()``:

```
sanitize_input(user_text)
  → redact_pii(sanitized)
    → rate_limit_check()          # raises RateLimitExceeded if exhausted
      → planner.run(clean_text)   # LLM call (may raise)
        → guardrail_output(summary)
          → Recommendation(...)
```

Each layer is a pure function in its own module under ``src/pia/safety/``:

| Module | Function | Responsibility |
|--------|----------|---------------|
| `sanitize.py` | `sanitize_input` | Strip ASCII control chars (except `\n`/`\t`), NFKC-normalise, trim, cap at 8 000 chars |
| `pii.py` | `redact_pii` | Regex-replace KZ IIN / phone / IBAN / email with safe placeholders |
| `ratelimit.py` | `rate_limit_check` | Token bucket, 10 req/min/process; raises `RateLimitExceeded` |
| `guardrail.py` | `guardrail_output` | Redact known credential tokens; hedge definitive financial calls |

### Layer-order rationale

1. **Sanitise first** — malformed control characters could confuse regex
   patterns in later layers; strip them before any matching.
2. **PII second** — redact user PII before it reaches the LLM or any
   logging/tracing layer.
3. **Rate-limit third** — check the budget before the potentially expensive
   LLM call; keeps the order cheap-to-expensive.
4. **LLM call** — the meaty part, intentionally isolated so degraded-path
   error handling is uniform.
5. **Guardrail last** — post-process LLM output; must see the final text.

### PII: regex baseline over Presidio

Presidio (Microsoft) is the de-facto NLP-backed PII redactor but requires
downloading a spaCy language model (~50MB) and adding a heavyweight
dependency.  For a capstone demo that needs to run `$0` on the grader's
laptop, this is disproportionate.

The Kazakhstan-specific patterns (12-digit IIN, +7/8 phone, KZ IBAN, email)
are well-defined and cover the realistic threat surface.  The regex baseline
was chosen because:

- No model download required.
- Zero false-negatives for the defined patterns (deterministic).
- Acceptable false-positives: a standalone 12-digit number that is not a real
  IIN will be redacted — conservative and appropriate for a financial context.

### Rate limit: 10 req/min process-local token bucket

A token bucket refilling at `capacity / 60 seconds` per second was chosen
over a fixed sliding window for smoother burst handling.  The capacity (10
req/min) is configurable via `Settings.rate_limit_per_minute` (from
``pyproject.toml`` → ``pia.config``) and overrideable by
``PIA_RATE_LIMIT_PER_MINUTE`` env var (for test isolation).

**Known tradeoff — process-local state does not survive Streamlit reloads.**
Each Streamlit hot-reload (file save) reinitialises the Python process and
resets the bucket.  This means an adversarial user who triggers a reload can
bypass the limit.  Acceptable for a capstone demo; a production deployment
would use Redis-backed counters.

A ``_reset()`` helper is exposed for test isolation; a conftest autouse
fixture calls it before every test so bucket exhaustion in one test does not
cascade to others.

### Guardrail subsumes the inline hedge

The prior inline ``_looks_like_definitive_call`` + ``_DEFINITIVE_CALL_TERMS``
check in ``planner.py`` was moved verbatim into ``guardrail.py``.  This makes
``guardrail_output`` the single canonical location for output safety — removing
duplicate logic and making it testable in isolation.

In addition, ``guardrail_output`` now redacts a small set of known credential
tokens sourced from ``tests/fixtures/adversarial_inputs.yaml`` (currently:
``{"hunter2"}``).  The set is intentionally small and defensible; credentials
visible in adversarial fixtures are the highest-confidence leak indicators.

## Consequences

**Positive**
- Single, well-named entrypoint per concern; each module is independently
  unit-testable.
- PII never reaches the LLM trace (Langfuse) in plaintext.
- Rate limiter protects LLM API costs during a live demo.
- `guardrail_output` is idempotent and covers both hedge and redaction in one
  pass.
- No new heavy dependencies (no spaCy, no Presidio, no Redis).

**Negative**
- Rate limiter is process-local: Streamlit reloads reset the bucket.
- Regex PII has false positives (12-digit financial amounts redacted as IIN).
- Known-leak token set is hand-curated; a production system needs a broader
  allow/deny list or ML classifier.

**Neutral**
- The `sanitize → redact → rate_limit → run → guardrail` order is documented
  here and in inline comments; deviating requires updating this ADR.

## Alternatives considered

- **Presidio (Microsoft NLP)** — rejected: spaCy model dependency is too
  heavy for a $0 grader path; regex covers all Kazakhstan-specific patterns.
- **Redis-backed rate limiter** — rejected: requires a running Redis instance;
  out of scope for capstone demo.
- **Single monolithic guard function** — rejected: harder to test, harder to
  extend; separation of concerns wins.
- **Separate guardrail microservice** — rejected: massive over-engineering for
  a single-process demo application.
