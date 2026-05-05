# Personal Investment-Planning Assistant

A multi-agent RAG + MCP system that helps a Kazakhstan-resident investor track holdings, monitor markets, and reallocate when conditions change. Course capstone (EPAM GenAI Engineering, 2026).

> Informational only. **Not** licensed financial, legal, or tax advice.

## What's inside

- 3 agents (Portfolio / Market / Planner) on an in-process Pydantic message bus.
- Hybrid RAG (BM25 + dense) over a real KZ-domain corpus, indexed in Weaviate.
- MCP: consumes a web-search server **and** ships a custom `kz-data` MCP with 4 tools (NBK rate, FX, KASE quote, deposit rates). One pooled subprocess per `advise()` call (`src/pia/mcp/session.py`).
- LLM and embedding providers are swappable via env vars (Anthropic / Gemini / Groq / Ollama / OpenAI / local).
- Streamlit chat UI with a portfolio sidebar and a **Diagnostics** expander (counters, p50/p95 latency, last Langfuse trace id).
- Layered safety facade (rate-limit → sanitize → PII redact → planner → output guardrail) with a structural Pydantic disclaimer on every `Recommendation`.

See `docs/superpowers/specs/2026-05-02-personal-investment-assistant-design.md` for the full design and `docs/decisions/` for ADRs.

## Runtime model

Local-only hybrid runtime: Weaviate runs in Docker; the Streamlit app runs as a local `uv` Python process. No cloud deployment or app container is required for the capstone.

## Quickstart

Requires `uv` (install: <https://docs.astral.sh/uv/>) and Docker.

```bash
git clone <repo> && cd task_1
cp .env.example .env             # edit if you want to use a paid LLM provider
uv sync --all-extras
docker compose up -d weaviate    # only container; the app runs locally via uv
uv run python -m scripts.ingest --reset   # populates Weaviate from data/
uv run streamlit run src/pia/ui/app.py    # chat UI on http://localhost:8501
```

CLI alternative (multi-command after Phase 4):

```bash
uv run python -m pia.cli ask "Should I rebalance my KZT savings into USD?"
uv run python -m pia.cli info
```

**First-run note:** the embedding model `BAAI/bge-m3` is downloaded to the local HuggingFace cache (~600MB) on first ingest or first chat turn. Subsequent runs reuse the cache.

The default config runs at $0: free Gemini LLM + local `BAAI/bge-m3` embeddings + self-hosted Weaviate.

**LLM key:** a working LLM key (Gemini, Anthropic, Groq, OpenAI, or Ollama) is required for live recommendations. Without one the chat returns a degraded "advisor unavailable" message and the not-financial-advice disclaimer still renders — Quickstart, ingest, and the UI itself still launch without a key so you can verify the setup.

## Tests

```bash
uv run pytest                    # unit + integration
uv run pytest -m smoke           # end-to-end
uv run pytest -m adversarial     # safety/jailbreak suite (post-draft)
```

## Layout

```
src/pia/    — agents, RAG, MCP, LLM client, config, UI (Streamlit entry: src/pia/ui/app.py)
data/       — corpus (personal holdings/plan/notes; public news, bank rates, KASE, NBK, Krisha)
scripts/    — CLI helpers (ingest, snapshots)
tests/      — unit, integration, fixtures
docs/       — brief, NFRs, success criteria, requirements addendum, ADRs, spec, plans
docker-compose.yml — Weaviate (only container; app runs locally via `uv`)
```

See `docs/superpowers/specs/2026-05-02-personal-investment-assistant-design.md` for the full spec and `docs/decisions/` for ADRs.

## License

MIT for code authored here. Third-party data is cited per source under `data/public/*/PROVENANCE.md`.
