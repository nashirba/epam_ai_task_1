# ADR 0012: Evaluation Harness — Thresholds, Gating, and Persisted Reports

- **Status:** Accepted
- **Date:** 2026-05-05
- **Deciders:** Project owner (Nurlan), AI pair
- **Related:** ADR 0001 (use ADRs); ADR 0008 (embeddings — drives retrieval); ADR 0010 (Langfuse observability — token counts feed eval reports).

## Context

ADRs 0001-0011 captured architecture and safety decisions. Evaluation was deliberately deferred and called out as an "ADR 0012 placeholder" in `docs/architecture_blueprint.md` §5: in v1, evaluation lived as concrete code (`src/pia/eval/retrieval.py`, `src/pia/eval/faithfulness.py`) plus fixtures (`tests/fixtures/golden_qa.yaml`, `tests/fixtures/retrieval_labels.yaml`, `tests/fixtures/adversarial_inputs.yaml`). That was honest, but it left three things implicit:

1. **What thresholds count as "passing"** — `tests/integration/test_retrieval_metric.py` asserts hit-rate@5 ≥ 0.6 and `tests/integration/test_faithfulness.py` asserts every score ≥ 1, but those numbers are not justified anywhere a grader can find them.
2. **How and why live-LLM tests are gated** — the `PIA_LIVE_LLM=1` env var convention exists in code but the rationale (CI without keys must still pass; faithfulness needs a real model) is undocumented.
3. **How evaluation results are persisted over time** — `docs/eval-runs/` exists but is empty, with no schema or retention policy.

Without these locked down, two failure modes are possible:

- A future contributor weakens a threshold to make a flaky test pass without surfacing the change as a deliberate quality decision.
- The executive summary cites "hit-rate@5 ≥ 0.6" but cannot reference the run that produced the number, weakening the +10 Data Quality bonus claim.

This ADR formalises the evaluation contract so the artifacts are auditable.

## Decision

### Three suites, three metrics, three thresholds

| Suite | Metric | Threshold | Driver | Fixture |
|---|---|---|---|---|
| **Retrieval** | Hit-rate@5 | ≥ 0.6 | `src/pia/eval/retrieval.py::evaluate_retrieval`, `hit_rate_at_k` | `tests/fixtures/retrieval_labels.yaml` (5 queries, EN+RU) |
| **Faithfulness** | LLM-as-judge score 0/1/2 | every case ≥ 1; mean ≥ 1.4 | `src/pia/eval/faithfulness.py::judge` | `tests/fixtures/golden_qa.yaml` (5 cases EN+RU) |
| **Adversarial** | Refusal-rate on definitive-call probes | 100% | `tests/adversarial/test_jailbreak.py` (and the broader 7-scenario suite for surfacing) | `tests/fixtures/adversarial_inputs.yaml` (7 scenarios) |

Threshold rationale:

- **0.6 hit-rate@5** — the labeled set has 5 queries; 0.6 means 3-of-5 expected sources surface in the top 5 chunks. Higher targets at this corpus size start gaming the labels rather than measuring retrieval quality. Re-evaluate when the labeled set grows past 20 cases.
- **Faithfulness ≥ 1 every case, mean ≥ 1.4** — score 0 (hallucination/contradiction) is a hard failure for a financial assistant; mean ≥ 1.4 keeps the bar above "everything partial" without requiring perfection on free-tier judge models.
- **100% refusal on definitive calls** — the structural guardrail (`guardrail_output` hedging EN+RU verbs, ADR 0011) makes this deterministic; any below-100% reading is a regression, not a flaky test.

### Live-LLM gating

Two-layer gate:

1. **Pytest marker** — `@pytest.mark.integration` for retrieval + faithfulness; `@pytest.mark.adversarial` for the safety probes.
2. **Env var** — `PIA_LIVE_LLM=1` required for any test path that calls `LLMClient.chat`.

Without `PIA_LIVE_LLM=1` set, faithfulness tests are skipped (not failed). CI without LLM keys still passes the unit suite. The maintainer's machine, the demo recording, and any committed eval run all set the env var explicitly.

The hit-rate@5 retrieval test does **not** require `PIA_LIVE_LLM` — it uses local embeddings + Weaviate only — so retrieval quality is verifiable on the `$0` path.

### Persisted-eval-runs convention

Eval runs are written to `docs/eval-runs/<YYYY-MM-DD>-<model_slug>-<suite>.json`.

Schema:

```json
{
  "run_id": "2026-05-05-gemini-2.0-flash-all-1",
  "timestamp": "2026-05-05T14:32:11Z",
  "model": "gemini/gemini-2.0-flash",
  "embedding_model": "BAAI/bge-m3",
  "suite": "all",
  "git_sha": "<short-hash>",
  "metrics": {
    "hit_rate_at_5": 0.8,
    "faithfulness": {
      "mean": 1.6,
      "min": 1,
      "max": 2,
      "scores": [2, 1, 2, 2, 1]
    },
    "adversarial": {
      "refusal_rate_definitive_call": 1.0,
      "scenarios_run": 7,
      "scenarios_passed": 7
    }
  },
  "fixtures": {
    "retrieval_labels": "tests/fixtures/retrieval_labels.yaml",
    "golden_qa": "tests/fixtures/golden_qa.yaml",
    "adversarial_inputs": "tests/fixtures/adversarial_inputs.yaml"
  }
}
```

Fields are nullable when the suite did not run (e.g., `faithfulness: null` when `PIA_LIVE_LLM` was unset). The harness writing these reports (`scripts/eval_report.py`) is built in a follow-up session — this ADR locks the schema first so the harness has a target.

Retention: keep all runs committed. Storage is negligible (one run ≈ 1 KB). Trend tracking is the whole point — deleting old runs defeats it.

### What is **not** in scope

- **Continuous integration** of the eval suite. The `$0` path keeps the unit suite in CI; live-LLM eval runs locally before submission and before the demo recording, not on every push.
- **Statistical significance testing.** Five-case fixtures cannot support t-tests honestly; threshold gates are the whole story at v1 corpus size. Re-open this when fixtures grow past 30 cases.
- **Cost dashboards.** Token counts are visible in the Langfuse dashboard when keys are set; an aggregated cost report is future work (`improvements.md` Session 4 metrics layer covers per-call counts but not money).

## Consequences

**Positive**
- Threshold rationale is auditable in one place; no future contributor can weaken a threshold silently.
- The executive summary can cite a specific run filename (`docs/eval-runs/...json`), making +10 Data Quality bonus claims defensible.
- The `PIA_LIVE_LLM` gate is documented, not just implemented — graders running CI without keys see the unit suite pass and the integration suite skip cleanly.
- Persisted runs are diffable: a regression that drops hit-rate@5 from 0.8 to 0.4 shows up in `git log docs/eval-runs/` immediately.
- Schema is locked before the writing harness is built — the harness has a target spec, not a moving one.

**Negative**
- Adds discipline overhead: every meaningful change to retrieval / chunker / embeddings should produce a fresh eval run before merge.
- The faithfulness judge is itself an LLM, so its scores have provider variance (Gemini Flash vs. Sonnet 4.6 will not agree on every case). Mitigated by recording `model` in every run; not mitigated for absolute comparability across providers.
- Adversarial refusal-rate is gated on the structural guardrail working — if the guardrail is bypassed (or the definitive-call verb list misses a phrasing), 100% becomes 0% and the threshold flips. Mitigated by the 7-scenario adversarial suite cross-checking the same property from different angles.

**Neutral**
- ADR 0012 is the **last** v1-scope ADR. Future ADRs (0013+) cover post-capstone work.

## Alternatives considered

- **Leave evaluation as code-plus-fixtures, no ADR.** This was the v1 stance. Rejected on second pass: the executive summary deliverable benefits materially from a threshold rationale a grader can find by ADR number. The cost of the ADR (this file) is one afternoon; the saved ambiguity is permanent.
- **Single combined "quality" threshold (e.g., a weighted score).** Rejected: hit-rate, faithfulness, and refusal-rate are independent failure modes. A weighted score hides which one regressed.
- **Persisted runs in a separate repo or in a database.** Rejected: the runs are tiny JSON files; committing them in `docs/eval-runs/` keeps everything in one git history, gives diffs for free, and matches the "rationale lives in the repo, not the chat" principle from ADR 0001.
- **Continuous-integration eval runs.** Rejected for v1: no live-LLM key in CI, no budget for paid runs, and the maintainer's pre-merge run is sufficient at single-user cadence. Re-open when there are multiple contributors.
- **Statistical significance gates instead of fixed thresholds.** Rejected: 5-case fixtures cannot support honest stats. Fixed thresholds are stricter and more legible at this scale.
