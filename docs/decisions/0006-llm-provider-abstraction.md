# ADR 0006: LLM Provider Abstraction via LiteLLM

- **Status:** Accepted
- **Date:** 2026-05-02
- **Deciders:** Project owner

## Context

The project must demonstrate code excellence, support a $0 grading run for reviewers, and ship in 16 days. Locking the system to a single LLM provider couples the codebase to vendor-specific tool-call formats and forfeits cost flexibility. The owner explicitly requested optionality between paid (best quality) and free (zero-cost) LLM models.

## Decision

Use **LiteLLM** as the single LLM client. All agent code goes through `LLMClient`, a thin wrapper that selects the provider via env var:

- `LLM_MODEL` — examples:
  - `anthropic/claude-sonnet-4-6` (paid; demo recommended)
  - `gemini/gemini-2.0-flash` (free hosted; best free tool-use)
  - `groq/llama-3.3-70b-versatile` (free hosted; fastest)
  - `ollama/qwen2.5` (fully local; offline-capable)
- `LLM_TEMPERATURE`, `LLM_MAX_TOKENS`.

Tool calling is unified by LiteLLM into the OpenAI tool-call schema; agents declare tools as JSON schema once.

A retry-with-repair loop wraps every agent's tool-call cycle: if a tool call fails JSON-schema validation, the model is re-prompted once with the validation error before the agent gives up. This raises tool-use reliability on free hosted models.

Prompt caching is enabled where supported (Anthropic). System prompts and tool schemas are placed in cache-eligible positions.

## Consequences

**Positive**
- Owner can swap models with `LLM_MODEL=…` without code changes.
- A grader can run the full system on a free Gemini key with zero LLM spend.
- Clear demonstration of a thoughtful design pattern (abstraction over vendor SDKs) for the +10 Code Excellence bonus.
- Future provider swaps (e.g., when Sonnet 4.7 ships) are a config change.

**Negative**
- LiteLLM lags occasionally behind native SDK features (e.g., new Anthropic features may take days to appear).
- Tool-use reliability differs significantly across models — explicitly known limitation. Demo will be recorded on Sonnet 4.6 for reliability; CI/dev runs on Gemini Flash. Tests must pass on at least one free provider.
- Streaming UX patterns are slightly more uniform but lose minor provider-specific affordances.

**Neutral**
- The wrapper class is a few hundred lines; we own it, satisfying the "own code" constraint.

## Alternatives considered

- **Anthropic SDK only.** Rejected. Forfeits free-grader path and cost flexibility.
- **Hand-rolled provider interface with one impl per provider.** Rejected. LiteLLM has done this; rebuilding is wasted effort against the timeline.
- **OpenRouter as the abstraction.** Considered. Acceptable backup, but LiteLLM is a Python library (no extra hop), supports `ollama` natively, and is more transparent.
