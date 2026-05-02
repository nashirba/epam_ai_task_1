# Personal Investment-Planning Assistant

A multi-agent RAG + MCP system that helps a Kazakhstan-resident investor track holdings, monitor markets, and reallocate when conditions change. Course capstone (EPAM GenAI Engineering, 2026).

> Informational only. **Not** licensed financial, legal, or tax advice.

## What's inside

- 3 agents (Portfolio / Market / Planner) on an in-process Pydantic message bus.
- Hybrid RAG (BM25 + dense) over a real KZ-domain corpus, indexed in Weaviate.
- MCP: consumes a web-search server **and** ships a custom `kz-data` MCP with 4 tools (NBK rate, FX, KASE quote, deposit rates).
- LLM and embedding providers are swappable via env vars (Anthropic / Gemini / Groq / Ollama / OpenAI / local).
- Streamlit chat UI with a portfolio sidebar.

See `docs/superpowers/specs/2026-05-02-personal-investment-assistant-design.md` for the full design and `docs/decisions/` for ADRs.

## Runtime model

Local-only hybrid runtime: Weaviate runs in Docker; the Streamlit app runs as a local `uv` Python process. No cloud deployment or app container is required for the capstone.

## Quickstart

```bash
git clone <repo> && cd task_1
cp .env.example .env             # edit if you want to use a paid provider
uv sync --all-extras
docker compose up -d weaviate
uv run python -m scripts.ingest  # populates Weaviate from data/
uv run streamlit run src/pia/ui/app.py
```

The default config runs at $0: free Gemini LLM + local `BAAI/bge-m3` embeddings + self-hosted Weaviate.

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
