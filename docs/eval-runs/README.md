# Persisted eval runs

This directory holds JSON reports from `scripts/eval_report.py`. Schema and threshold rationale are locked in [ADR 0012](../decisions/0012-evaluation-harness.md); the harness produces the file, the ADR explains the contract.

## File naming

```
<YYYY-MM-DD>-<model_slug>-<suite>.json
```

`model_slug` replaces `/` with `-` (e.g. `gemini/gemini-2.0-flash` → `gemini-gemini-2.0-flash`). Same-day re-runs against the same model+suite append `-2`, `-3`, … to the filename so previous runs are preserved (retention: keep all runs committed; storage is ~1 KB per file).

## Schema

Mirrors the spec in [ADR 0012 §Persisted-eval-runs convention](../decisions/0012-evaluation-harness.md#persisted-eval-runs-convention). Top-level keys: `run_id`, `timestamp`, `model`, `embedding_model`, `suite`, `git_sha`, `metrics`, `fixtures`, `tokens_total`. Nullable when the suite was skipped (e.g. `metrics.faithfulness == null` when `PIA_LIVE_LLM` was unset).

## Running

```bash
# free-tier $0 path (Gemini Flash + local BAAI/bge-m3)
LLM_MODEL=gemini/gemini-2.0-flash PIA_LIVE_LLM=1 \
    uv run python -m scripts.eval_report --suite all

# retrieval-only (no LLM key needed)
uv run python -m scripts.eval_report --suite retrieval
```

Pre-flight: `docker compose up -d weaviate` and `uv run python -m scripts.ingest --reset` if the `KB` collection is empty. Without `PIA_LIVE_LLM=1`, faithfulness and adversarial blocks are written as `null` — retrieval still runs because it hits local embeddings + Weaviate only.

## Suites

- **retrieval** — `tests/fixtures/retrieval_labels.yaml`, hit-rate@5 (threshold ≥ 0.6).
- **faithfulness** — `tests/fixtures/golden_qa.yaml`, LLM-as-judge 0/1/2 (threshold every score ≥ 1, mean ≥ 1.4). Live-LLM-gated.
- **adversarial** — `tests/fixtures/adversarial_inputs.yaml`, replays each scenario through `advise()` and records pass/fail plus `refusal_rate_definitive_call` (threshold = 1.0 on the `a2_jailbreak_definitive_call` probe). Live-LLM-gated.

`tokens_total` is reserved for a future Langfuse export pass and is currently `null`.

## Free-tier caveat

`gemini/gemini-2.0-flash` is the project's `$0` LLM path. Its free quota (per-minute and per-day) is shared with day-to-day debugging, so a single `--suite all` run can exhaust the daily budget mid-faithfulness. Symptoms in the JSON: `metrics.faithfulness.scores: []` with `RateLimitError` strings under `details[].error`, and `metrics.adversarial.details[].degraded: true` (every `advise()` returns the safety facade's "advisor temporarily unavailable" message instead of a model response). The harness records this state honestly rather than retrying — `tests/integration/test_faithfulness.py` and `tests/adversarial/*.py` cover those thresholds against a fresh quota window when needed. Set `PIA_EVAL_DELAY_SECONDS=20` (default `5`) to space requests if the per-minute quota is the only constraint.
