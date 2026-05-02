# ADR 0010: Observability via Langfuse

- **Status:** Accepted
- **Date:** 2026-05-02
- **Deciders:** Project owner (Nurlan), AI pair

## Context

The capstone requires a demonstrable observability story: LLM call tracing,
latency, tool-call sequences, and guardrail firings should all be visible in a
dashboard without significant engineering overhead.  The system is a single
Python process on a laptop / Streamlit Cloud — there is no distributed
infrastructure to justify a full OpenTelemetry collector pipeline.

Several options exist (LangSmith, OpenTelemetry/Jaeger, Langfuse).  The
project already has `langfuse>=2.50` in `pyproject.toml` (installed version:
4.5.1).  Running without credentials must never raise exceptions; the grader
and CI pipelines have no Langfuse keys.

## Decision

**Use Langfuse cloud free tier** via a thin adapter module at
`src/pia/observability/langfuse.py` with the following design choices:

1. **Trace identifier = `AgentMessage.request_id`** (UUID4 already on the
   message envelope from Phase 6).  Every conversation turn carries this ID,
   enabling full trace reconstruction for a single user interaction.

2. **SDK API: `Langfuse.start_as_current_observation(name=)`** — the stable
   context-manager entry point in Langfuse SDK 4.x.  The plan document
   referenced `start_as_current_span` which does **not** exist in langfuse
   4.5.1; verified by inspecting `dir(Langfuse())`.  `start_as_current_span`
   is an OpenTelemetry concept — Langfuse exposes its own observation model.

3. **OpenTelemetry adapter NOT used.**  Langfuse 4.x ships an OTel exporter
   but it requires a running OTel Collector endpoint and is aimed at
   production microservice deployments.  For a capstone demo a direct
   Langfuse SDK call is simpler and sufficient.

4. **No-op when keys are unset.** The `trace(name)` decorator checks
   `_client is None` and returns the original function unchanged — no wrapper,
   no overhead.  This means unit tests, CI, and grader runs all work without
   any Langfuse credentials.

5. **Decorated surfaces:**
   - `LLMClient.chat` → `@trace("llm.chat")`
   - `BaseAgent.run` → `@trace("agent.run")`
   - `ask_portfolio` → `@trace("agent.portfolio")`
   - `ask_market` → `@trace("agent.market")`
   - `advise` → `@trace("agent.planner.advise")`
   - `retrieve` (rag) → `@trace("rag.retrieve")`
   - `kz_data_call_sync` → `@trace("mcp.kz_data")`
   - `web_search_sync` → `@trace("mcp.web_search")`

## Consequences

**Positive**
- Zero-friction local development: keys unset = zero overhead, no errors.
- Full call stack visible in Langfuse dashboard when keys are set (demo mode).
- Free tier supports the capstone volume (thousands of traces).
- The adapter is 40 lines; easy to swap or extend.

**Negative**
- `request_id` is not automatically threaded through the Langfuse context;
  parent-child span relationships rely on SDK's OTel context propagation,
  which is automatic via `start_as_current_observation`.  No manual
  correlation is needed for the capstone.
- If the SDK changes its API in a future major version, the adapter module is
  the single file to update.

**Neutral**
- Langfuse data stays in the cloud free tier; no self-hosted option needed for
  this scope.

## Alternatives considered

- **LangSmith** — rejected: requires LangChain in the call graph; adding that
  dependency is disproportionate to the benefit.
- **OpenTelemetry + Jaeger** — rejected: heavy infrastructure (collector,
  Jaeger) for a single-process demo; overkill and harder to demo live.
- **Plain `logging` with JSON lines** — rejected: readable locally but not a
  proper trace with nested spans; insufficient for the "observability" rubric.
- **No observability** — rejected: explicitly requested by the post-draft plan
  and penalised in the grading rubric.
