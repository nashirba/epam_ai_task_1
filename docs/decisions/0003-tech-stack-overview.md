# ADR 0003: Tech Stack Overview

- **Status:** Accepted
- **Date:** 2026-05-02
- **Deciders:** Project owner

## Context

A 16-day timeline with vibecoding-paced AI-assisted development. The system must run locally as a real application (not a notebook), satisfy "own code" for core agentic logic, and be friendly to a grading reviewer who clones the repo and follows a short local quickstart.

## Decision

Single Python service. Stack:

| Layer | Choice | Notes |
|---|---|---|
| Language | Python 3.12 | mature AI ecosystem, owner is fluent |
| Env / deps | `uv` + `pyproject.toml` | fast resolver, reproducible |
| Lint / format | `ruff` + `ruff format` | one tool, fast |
| Tests | `pytest`, `pytest-asyncio`, `pytest-mock` | standard |
| LLM client | LiteLLM (see ADR 0006) | provider abstraction |
| Vector store | Weaviate (see ADR 0007) | hybrid search, self-hosted Docker |
| Embeddings | provider-abstracted (see ADR 0008) | hosted or local |
| MCP server | FastMCP | minimal Python boilerplate |
| MCP client | official `mcp` SDK | reference implementation |
| UI | Streamlit | fastest path to "investor-ready" demo |
| Observability | Langfuse free tier | one decorator per agent/LLM call |
| Validation | Pydantic v2 | message bus types, structured outputs |
| Local runtime | `uv` + Docker Compose | app runs as a local Streamlit process; Weaviate runs in Docker |

## Consequences

**Positive**
- Every component has strong AI-coding-assistant familiarity → vibecoding stays smooth.
- Single language reduces context-switching cost.
- The hybrid local runtime satisfies the "real application, not notebook" requirement while keeping reviewer setup simple.

**Negative**
- Python tool-use code is more verbose than equivalent TypeScript SDKs in some places.
- Streamlit is functional but not as polished as a custom React UI; mitigated by careful component design.

**Neutral**
- Stack is conservative and "boring" — not a downside given the timeline; ADRs are where architectural creativity is shown.

## Alternatives considered

- **TypeScript / Next.js stack with LangChain.js** — rejected: weaker MCP and Weaviate Python-side maturity, owner less fluent.
- **FastAPI + a custom React UI** — rejected: the +10 UX bonus does not require a full SPA; Streamlit + a tight design clears the bar at much lower cost.
- **Notebooks for the demo** — rejected outright by the meeting requirements (`q_a_meetings_2`, lines 41-49).
