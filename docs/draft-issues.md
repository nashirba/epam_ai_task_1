# Draft Issues — Punch List

**Created:** 2026-05-02
**Source:** Phase 6 of `docs/superpowers/plans/2026-05-02-pia-pre-draft.md`
**Purpose:** input for the Days 8-16 post-draft plan. Each item is deferred work
that did not block the `v0.1.0-draft` end-to-end milestone but must be addressed
before submission.

---

## 1. Deferred manual smoke (Phase 6 Task 6.1)

The pre-draft plan calls for triaging 5 representative queries through the
Streamlit UI on Day 7. **Skipped** in this environment: no LLM API key was
available, so the chat path could not be exercised end-to-end.

- [ ] Run the Streamlit UI with a working LLM key (`GEMINI_API_KEY` is the
      cheapest default) and exercise at least these 5 query types:
  1. Holdings/portfolio question (exercises Portfolio agent + RAG over the
     personal corpus).
  2. Market/news question in Russian (exercises Market agent + multilingual
     hybrid retrieval).
  3. Reallocation question that should produce a `Recommendation` with a hedge
     (exercises Planner orchestration + disclaimer guardrail).
  4. NBK rate / FX / KASE quote question (exercises `kz-data` MCP).
  5. Adversarial / out-of-scope question (exercises refusal path; full
     adversarial suite is post-draft, this is a single sanity probe).
- [ ] For each issue found, log it here under "Triage findings" and fix the
      top 3-5 by user-visible severity (no Python tracebacks in the chat,
      tool-call timeouts surfaced cleanly, refusals where required).

---

## 2. Polish items deferred from Phases 2-4

Consolidated from the "Deferred to Phase 6 polish" notes in commits
`93f8545`, `71df2a4`, and `d753727`, plus the "Known omissions for this
plan" section of the pre-draft plan.

### RAG / chunker / store

- [ ] **Chunker: heading text duplication into chunk body.** The chunker emits
      a heading and a body chunk; the heading text is stored separately and is
      not concatenated into the body, hurting BM25 recall when the heading
      contains the only mention of an entity. Fix: prepend heading text to the
      first body chunk under each heading. (See `src/pia/rag/chunker.py`.)
- [ ] **Store: `published_at` stored as TEXT vs DATE.** Weaviate schema currently
      uses TEXT for the `published_at` property. Decision pending: keep TEXT and
      parse on read, or change to DATE and reingest. Document the chosen path
      as **ADR-009** in post-draft. (See `src/pia/rag/store.py`.)
- [ ] **Ingest: chunker `max_tokens=120` override.** Current 120-token cap was a
      conservative starting point; raising it to 250-350 should improve answer
      quality for question types that need multi-sentence context. Requires the
      chunker heading fix above first. (See `scripts/ingest.py`.)

### Embeddings

- [ ] **LiteLLM embeddings: silent dim fallback for unknown models.** When the
      configured embedding model is unrecognized, the wrapper falls back to a
      default dimension without raising. Add an explicit error or warning so
      mismatched dims (which corrupt the Weaviate index) cannot happen
      silently. (See `src/pia/embeddings/litellm.py`.)

### MCP

- [ ] **`kz_data_call` returns JSON-string.** The current contract returns a
      JSON string the caller must parse. Either add a `kz_data_call_json` parsed
      variant or document the contract clearly in the tool docstring.
      (See `src/pia/mcp/clients/kz_data.py`.)
- [ ] **`web_search` payload shape (Tavily content unwrap).** The current
      wrapper returns the raw Tavily response; richer citations need the
      `content` field unwrapped per result. (See
      `src/pia/mcp/clients/tavily.py`.)
- [ ] **`get_nbk_rate(date_str=None)` `as_of` semantic.** When `date_str` is
      omitted, should `as_of` mean today's date or the rate's `effective_from`?
      Pick one and assert it in a unit test. (See
      `src/pia/mcp/tools/nbk.py`.)
- [ ] **Subprocess pooling for repeated MCP calls.** Each MCP tool call
      currently spawns a fresh subprocess. In a single agent loop with 3-5 tool
      calls this is the dominant latency. Pool the FastMCP subprocess for the
      duration of a request. (See `src/pia/mcp/clients/`.)

### LLM client / agent loop

- [ ] **Tool-call response shape adapter (dict vs Pydantic).** Different
      providers return tool calls as dicts vs Pydantic objects; the current
      adapter handles the common shapes but was not exercised against a live
      LLM. Add a normalization layer plus a fixture-driven unit test. (See
      `src/pia/llm/client.py`.)

### Tests

- [ ] **BaseAgent loop unit tests.** Add coverage for: invalid-JSON tool-args
      path, unknown-tool-name path, budget-exhausted path. (See
      `src/pia/agents/base.py`, `tests/unit/agents/`.)
- [ ] **`advise()` always-returns-Recommendation test.** Confirm that the
      Planner wrapper always returns a `Recommendation` with the disclaimer,
      even when the inner planner.run raises. (See
      `src/pia/agents/planner.py`, `tests/unit/agents/`.)

### UI (from "Known omissions")

- [ ] **Allocation pie chart.** Current Phase 5 sidebar uses bar charts for
      allocation/currency breakdowns. Replace allocation with a pie chart in
      post-draft polish. (See `src/pia/ui/app.py`.)

---

## 3. Post-draft binding requirements

From the pre-draft plan's "Post-Draft Required Coverage" section, mapped
back to `docs/requirements_addendum.md`,
`docs/non_functional_requirements.md`, and `docs/success_criteria.md`.

### Tests (positive + adversarial)

- [ ] Prompt-injection probes (system-prompt extraction, tool hijack).
- [ ] Jailbreak refusal under fuzzing variants.
- [ ] Irrelevant / out-of-scope query handling.
- [ ] Retrieval-miss handling (query for a topic not in the corpus).
- [ ] MCP timeout / error paths (kz-data subprocess crash, Tavily 5xx).
- [ ] PII probe (input contains an IIN / phone number / address).
- [ ] Hallucination probe (LLM-as-judge on a small golden set).
- [ ] Source-conflict scenario (two retrieved docs contradict).

### Observability (Langfuse)

- [ ] Langfuse tracing on agent / LLM / tool calls (ADR-006 path is
      provider-neutral; Langfuse plugs in at the LiteLLM client layer).
- [ ] Basic metrics (request count, tool-call count, p50/p95 latency).
- [ ] Structured error logging with correlation IDs per request.
- [ ] Either a Langfuse dashboard link or an in-app diagnostics view.

### Safety guardrails

- [ ] Input sanitization layer (strip control chars, length cap, prompt-marker
      stripping).
- [ ] Content filtering for off-topic / disallowed asks.
- [ ] PII detection and redaction (Presidio or richer regex over the current
      stub).
- [ ] Rate limiting on the agent entrypoint (per-session token bucket is
      enough for the local single-user runtime).
- [ ] Graceful degraded-answer behavior on each failure mode (already partially
      shipped in Phase 4 wrapper; needs explicit tests).

### RAG QA evals

- [ ] Retrieval@k checks (precision/recall on a labeled query set).
- [ ] Source attribution tests (every claim in the answer maps to a retrieved
      chunk).
- [ ] Faithfulness / hallucination checks (LLM-as-judge with a threshold).

### Local runtime polish

- [ ] README quickstart reproducible from a fresh clone (covered minimally in
      `v0.1.0-draft`; needs a CI smoke run to prove it).
- [ ] Local-only access-control note (Streamlit binds to localhost; document
      it).
- [ ] Reproducible smoke-test commands (`uv run pytest -m smoke` after
      `docker compose up -d weaviate` + ingest).

### Deliverables (course submission)

- [ ] Architecture Blueprint document.
- [ ] Self-Review document.
- [ ] Executive Summary document.
- [ ] Video Demo recording + link.
- [ ] `Capstone_project_<First>_<Last>.txt` submission file.

### Other "Known omissions" (post-draft)

- [ ] Cross-encoder reranker on top of hybrid retrieval.
- [ ] LLM-as-judge eval harness with golden-set scoring and thresholds.
