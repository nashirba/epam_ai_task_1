# Personal Investment-Planning Assistant — Executive Summary

- **Project:** Personal Investment-Planning Assistant (PIA)
- **Author:** Nurlan
- **Audience:** Capstone review committee, prospective stakeholders.
- **Length:** 1-2 pages.

## Problem

A Kazakhstan-resident individual investor with capital but limited time faces a fragmented information landscape: NBK base-rate moves, bank deposit-rate sheets that differ by currency and term, KASE-listed equities with thin English coverage, Almaty residential listings on Krisha.kz, KZT/USD/EUR swings, and Russian-language news. Monitoring these by hand is expensive: idle KZT cash earns less than a current Halyk 12-month deposit, missed reallocation moments leave hard-currency exposure off-target, and licensed advisors are too expensive for a single retail investor. The result is a real, recurring loss of money and confidence — and a market that is small enough that off-the-shelf international robo-advisors do not serve it.

## Solution

A multi-agent assistant that combines a private knowledge base of the user's holdings, plan, and notes with live KZ market data, and produces evidence-backed recommendations with citations and a non-removable compliance disclaimer. Three agents — Portfolio (RAG over personal notes), Market (MCP-driven live data), and Planner (orchestrator and synthesizer) — cooperate over a typed Pydantic message bus inside a single Python process. Safety is structural, not stylistic: the disclaimer is a Pydantic field on every `Recommendation`, and a layered facade (rate-limit → sanitize → PII-redact → planner.run → output guardrail) wraps the user-facing entry point. The product is a local Streamlit app the user runs on their own laptop; a `docker compose up -d weaviate` plus `uv run streamlit run` is the entire deployment.

## Key technical decisions

- **Hybrid RAG (Weaviate BM25 + dense)** over a real KZ corpus: 37 news articles (RU+EN), 6 bank deposit-rate sheets, KASE/NBK snapshots, Krisha.kz listings, plus the user's own holdings, plan, and 5 investment-thesis notes. ADR 0007.
- **Custom `kz-data` MCP server** (FastMCP, 4 tools: NBK rate, FX, KASE quote, deposit rates) plus a consumed Tavily web-search MCP. Demonstrates protocol mastery — building, not just consuming. ADR 0005.
- **Provider abstraction via LiteLLM and a pluggable `EmbeddingProvider`** lets `LLM_MODEL` and `EMBEDDING_PROVIDER` be set by env var. Free Gemini Flash + local `BAAI/bge-m3` embeddings + self-hosted Weaviate gives a reproducible **`$0` grader path**; paid Sonnet 4.6 is the demo path. ADRs 0006, 0008.
- **Compliance disclaimer is a Pydantic field** on every `Recommendation`, not a model-discretion string. `advise()` always returns a valid `Recommendation` even when the inner planner raises — proven by `tests/unit/test_planner_disclaimer.py`. The output guardrail (`guardrail_output`) hedges definitive buy/sell calls in EN and RU and redacts known credential tokens. ADRs 0010, 0011.
- **Eleven ADRs (0001-0011)** capture the meaningful technical decisions. They are written at the time of the decision, not retroactively, and the Architecture Blueprint and demo voiceover both reference them by number.

## Results

- **86 automated tests pass**: 66 unit (agents, RAG, MCP tools, safety facade, disclaimer), 13 integration (golden Q&A end-to-end, hit-rate@5 retrieval metric, faithfulness LLM-judge, MCP subprocess round-trip, Weaviate hybrid search), and 7 adversarial (prompt injection in a planted note, jailbreak / definitive-call refusal, irrelevant query, source conflict, MCP timeout, PII probe, hallucination probe).
- **Hit-rate@5 ≥ 0.6** on the labeled retrieval set (`tests/fixtures/retrieval_labels.yaml`); **faithfulness LLM-judge ≥ 1** on every golden Q&A case (`tests/fixtures/golden_qa.yaml`, scoring 0/1/2).
- **Streamlit UI** ships citations as a Sources expander, allocation and currency-exposure donut charts, a freshness pill summarizing the oldest snapshot date, and an `st.error` "advisor unavailable" graceful state with a Try-again button when an upstream tool fails.
- **Reproducible local-only quickstart**:
  ```bash
  uv sync --all-extras
  docker compose up -d weaviate
  uv run python -m scripts.ingest --reset
  uv run streamlit run src/pia/ui/app.py
  ```
  First-run cost dominated by the one-time `~600MB` `BAAI/bge-m3` download.

## Business value

- **Time savings for a high-earning, time-poor investor.** The target user spends their week writing software, not reading NBK announcements; the assistant collapses a recurring weekly hour into a chat-driven check-in.
- **Defensible recommendations.** Every actionable claim cites the source it draws from; every recommendation is hedged and carries the disclaimer; tool failures degrade gracefully rather than hallucinating numbers. This is what makes the product safe to use with real capital — and what would let it pass a future compliance review.
- **Locally deployable, extensible to a wider Kazakhstan retail-investor audience.** The single-user local shape was a v1 simplification; the underlying architecture (typed message bus, MCP for data, hybrid RAG, LiteLLM abstraction) generalizes cleanly to a multi-tenant deployment if the user-research case is made.

## Limitations and next steps

Honest about what v1 does *not* do:

- **Snapshot data, not live refresh.** The corpus under `data/public/` is committed snapshots; a live refresh job is the most impactful next step (~1 day of work, drawn from `docs/draft-issues.md` post-draft binding requirements).
- **Asset coverage is v1-bounded.** Crypto, gold, UAPF, AIX bonds, and mutual funds are out of scope per ADR 0002; obvious "next steps" for a v2.
- **Single-user; no authentication.** The Streamlit app binds to localhost. A multi-tenant deployment would need session storage, per-user data isolation, and an auth layer.
- **Resource and metrics surface is partial.** Today only Langfuse spans are emitted (when keys are set); request count, p50/p95 latency, tool-error rate, and refusal-rate counters are not exposed. An in-app diagnostics tab is a clean ~1-day add.
- **MCP subprocess pooling not implemented.** Each `kz_data_call_sync` spawns a fresh subprocess; pooling per-`advise()`-call is an obvious latency win without architectural change.
- **Persisted eval reports under `docs/eval-runs/` not wired up.** The directory exists; a small harness that writes per-run JSON (model, fixture, scores) would let stakeholders track quality over time without re-running pytest.

---

> Informational only. **Not** licensed financial, legal, or tax advice. Consult a licensed professional before acting.
