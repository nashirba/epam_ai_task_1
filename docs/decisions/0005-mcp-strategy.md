# ADR 0005: MCP Strategy — Consume Web-Search MCP and Build a Custom KZ-Data MCP Server

- **Status:** Accepted
- **Date:** 2026-05-02
- **Deciders:** Project owner

## Context

The brief requires "at least one external data source or tool connected via MCP." The +10 Code Excellence bonus and demo narrative both reward demonstrating depth of MCP understanding, not just consumption.

KZ-specific data sources (NBK, KASE, Krisha, bank rate pages) have no off-the-shelf MCP server. Web search is widely available as MCP (Tavily, Brave).

## Decision

Two MCP integrations:

1. **Consume** an off-the-shelf web-search MCP. Default: **Tavily MCP**. Fallback: **Brave Search MCP**.
2. **Build** a custom MCP server `kz-data` using **FastMCP**, exposing four tools:
   - `get_nbk_rate(date?: str)` — NBK base rate, FX (KZT/USD, KZT/EUR, KZT/RUB), gold price.
   - `get_fx_rate(pair: str, date?: str)` — FX spot or historical.
   - `get_kase_quote(ticker: str)` — KASE snapshot.
   - `get_deposit_rates(currency: str, term_months: int)` — bank deposit rates from a small bank set.

Each tool is backed by snapshot files committed to the repo (with `last_updated` timestamps), so the server is fully reproducible without live scraping during the demo. The `last_updated` is surfaced in tool responses so agents can reason about staleness.

The custom MCP runs as a subprocess over the standard MCP transport. The Market Agent is the only consumer in v1.

## Consequences

**Positive**
- Demonstrates building an MCP server, not just consuming one — a stronger code-excellence narrative.
- Snapshot-backed tools are deterministic, testable, and immune to network failures during the demo.
- Cleanly separates KZ-specific data fetching from agent code.
- The custom MCP is independently runnable and presentable — useful demo asset.

**Negative**
- Snapshots go stale if the project is run months later — accepted; refreshing is "future work."
- A second MCP transport adds one more moving part to the dev experience; mitigated by `docker-compose` and a CLI helper.

**Neutral**
- Could swap Tavily for any other web-search MCP. Tavily chosen for its free tier; Brave is the equally-acceptable backup.

## Alternatives considered

- **Consume only.** Rejected. Weakens the demo narrative; the brief minimum is met but the +10 Code Excellence bonus benefits from building.
- **Build only (no third-party consumption).** Rejected. Reinventing web search is wasteful and the breadth of MCP integration is worth showing.
- **Build a much larger custom MCP (10+ tools).** Rejected. Each extra tool adds scraping work; four covers the demo and tests, more is YAGNI for v1.
- **Use HTTP APIs directly without MCP.** Rejected. Violates the explicit MCP requirement; also loses the protocol-level uniformity that makes the agents simpler.

## Addendum (2026-05-05) — Per-request kz-data subprocess pooling

In v1, every `kz_data_call_sync` spawned a fresh `python -m pia.mcp.server` subprocess. A typical `advise()` run with 3-5 tool calls paid 3-5× the FastMCP startup cost, which dominated end-to-end latency.

`pia.mcp.session.MCPSessionSync` now owns one stdio subprocess + one `ClientSession` for the lifetime of one `advise()` call, backed by a daemon thread running its own asyncio loop. Tool calls dispatch onto that loop via `asyncio.run_coroutine_threadsafe`. Activation is opt-in via a `ContextVar` (`bind_kz_data_session`) so unit tests and ad-hoc CLI calls keep working without a pool.

`advise()` opens the pool on entry and closes on exit. If the pool fails to open (e.g., FastMCP missing, OS hand-off error), the call falls back to the per-call subprocess path inside `kz_data_call_sync` rather than failing the whole request. Tavily web search is **not** pooled in v1 — different binary (`npx`), called at most once per request, pooling cost outweighs the win.

The "MCP performance" entry under `architecture_blueprint.md` §8 should now be considered partially closed.
