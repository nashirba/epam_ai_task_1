# ADR 0013: LLM Rate-Limit Resilience — Retries and Graceful Degradation

- **Status:** Accepted
- **Date:** 2026-05-18
- **Deciders:** Project owner (Nurlan), AI pair
- **Related:** ADR 0006 (LLM provider abstraction); ADR 0011 (Safety layered facade).

## Context

The default `LLM_MODEL` is `gemini/gemini-2.0-flash`, chosen in ADR 0006 to keep
the grader path zero-cost. Gemini's free tier has a low RPM ceiling
(≈15 requests / minute for `gemini-2.0-flash`). A single user turn drives:

- 1 Planner LLM call to decide which sub-agent to invoke,
- up to 8 tool-call iterations per Portfolio + Market sub-agent
  (`BaseAgent.max_tool_calls = 8`),
- a final Planner synthesis call.

In the worst case one user query produces ~17 provider-side LLM calls.
A grader exploring the demo (or our own eval harness) trips the quota
within seconds, surfacing as `litellm.RateLimitError`. The UI rendered
this as the opaque message:

> The advisor is temporarily unavailable (RateLimitError). Please try again in a moment.

Two problems:

1. **No retry**: a single transient 429 fails the whole turn. Gemini
   recovers within seconds; the client never tries again.
2. **Generic error surface**: users (and graders) can't distinguish
   "provider throttled me" from "agent crashed". The remediation
   ("wait ~30s") is hidden behind a stack-trace class name.

## Decision

Two changes, both small:

1. **Retry transient errors at the LLM client boundary.** `LLMClient.chat`
   forwards `num_retries=N` to `litellm.completion`. LiteLLM applies
   exponential backoff internally for retryable failures (rate-limit,
   timeout, transient 5xx). `N` is configurable via the
   `LLM_NUM_RETRIES` env var (default `3`), declared on
   `pia.config.Settings`.
2. **Surface rate-limit explicitly in the planner facade.**
   `pia.agents.planner._advise_inner` catches `litellm.RateLimitError`
   ahead of the broad `Exception` arm and returns:

   > The LLM provider is temporarily rate-limiting requests. Please wait ~30 seconds and try again.

   The Streamlit UI marker list (`_DEGRADED_MARKERS`) recognises the
   new phrase so it still renders as `st.error` with the Try-again button.

## Tuning constants (learned from live runs 2026-05-18)

Experimental TPM/TPD reproduction showed three additional levers had
to move together for free-tier survival:

| Setting | Old | New | Reason |
|---|---|---|---|
| `Settings.llm_max_tokens` (default + `.env`) | 2048 | 512 | Each call reserves `max_tokens` against Groq's TPM bucket; 2048 × 9 calls/turn = 18 432 > 12 000 TPM. 512 fits with headroom. |
| `BaseAgent.max_tool_calls` | 8 | 5 | Cuts worst-case calls per turn from ~18 to ~12 without starving planner synthesis. |
| `Settings.llm_num_retries` | 3 | 6 | Exponential backoff of ~63s covers a full TPM 60s rolling-window refill on Groq. |

These are tuning, not architecture; further changes (e.g. switching
defaults to a paid provider) belong in a follow-up ADR.

## Consequences

**Positive**
- Free-tier Gemini demo recovers from short 429 bursts without user
  intervention; matches the "grader runs cost $0" promise in ADR 0006.
- Users see actionable wording when the provider throttles, separate
  from a true outage.
- `num_retries` is per-instance, so eval harness can disable retries
  (`LLMClient(num_retries=0)`) to keep eval reports deterministic.

**Negative**
- A genuinely degraded provider now takes longer to fail (retries +
  backoff). Acceptable: the planner already calls the LLM many times
  per turn; one extra `~4 + 8` seconds in the worst case is dominated
  by tool-call latency.
- Retried requests still count against Langfuse token totals on
  successful retries; failed retries are not currently traced
  individually (LiteLLM swallows intermediate attempts). Acceptable
  for the capstone; could be revisited if we ever do paid-tier QPS
  budgeting.

**Neutral**
- No new dependency. LiteLLM ≥ 1.55 already supports `num_retries`.

## Alternatives considered

- **Lower `BaseAgent.max_tool_calls`.** Rejected — masks the symptom
  by clipping legitimate work; some user queries genuinely need
  multiple tool calls.
- **Switch default to a paid provider (Sonnet 4.6).** Rejected for the
  default path; the zero-cost grader promise comes first. The owner
  can still set `LLM_MODEL=anthropic/claude-sonnet-4-6` for the demo
  recording.
- **App-level token bucket throttle before calling LLM.** Rejected —
  duplicates work LiteLLM does correctly and adds latency to every
  call instead of only the failing ones.
