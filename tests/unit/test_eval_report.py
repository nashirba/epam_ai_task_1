"""Unit tests for the persisted-eval-report harness (`scripts/eval_report.py`).

Cover the pure helpers only — the live-LLM suite runners are exercised by the
real eval runs committed under `docs/eval-runs/`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.eval_report import (
    _build_report,
    _check_forbidden,
    _filename_for,
    _next_run_counter,
    _run_id,
    _score_scenario,
    _slug,
)


def test_slug_replaces_slash_with_dash():
    assert _slug("gemini/gemini-2.0-flash") == "gemini-gemini-2.0-flash"


def test_slug_passes_through_safe_chars():
    assert _slug("openai-gpt-4o-mini") == "openai-gpt-4o-mini"


def test_filename_format_matches_adr_0012():
    name = _filename_for("2026-05-10", "gemini-gemini-2.0-flash", "all")
    assert name == "2026-05-10-gemini-gemini-2.0-flash-all.json"


def test_run_id_format_includes_counter():
    rid = _run_id("2026-05-10", "gemini-gemini-2.0-flash", "all", 1)
    assert rid == "2026-05-10-gemini-gemini-2.0-flash-all-1"


def test_next_run_counter_starts_at_one_when_dir_empty(tmp_path: Path):
    assert _next_run_counter(tmp_path, "2026-05-10", "gemini-gemini-2.0-flash", "all") == 1


def test_next_run_counter_bumps_when_same_day_file_exists(tmp_path: Path):
    (tmp_path / "2026-05-10-gemini-gemini-2.0-flash-all.json").write_text("{}")
    assert _next_run_counter(tmp_path, "2026-05-10", "gemini-gemini-2.0-flash", "all") == 2


def test_check_forbidden_detects_violations():
    assert _check_forbidden("you should buy HSBK now", ["you should buy"]) == ["you should buy"]


def test_check_forbidden_is_case_insensitive():
    assert _check_forbidden("YOU SHOULD BUY", ["you should buy"]) == ["you should buy"]


def test_check_forbidden_returns_empty_when_clean():
    assert _check_forbidden("hedged: consider this option", ["you should buy"]) == []


def test_build_report_includes_locked_schema_keys():
    report = _build_report(
        date="2026-05-10",
        timestamp="2026-05-10T12:00:00Z",
        model="gemini/gemini-2.0-flash",
        embedding_model="BAAI/bge-m3",
        suite="all",
        git_sha="abc1234",
        counter=1,
        metrics={
            "hit_rate_at_5": 0.8,
            "faithfulness": None,
            "adversarial": None,
        },
        fixtures={
            "retrieval_labels": "tests/fixtures/retrieval_labels.yaml",
            "golden_qa": "tests/fixtures/golden_qa.yaml",
            "adversarial_inputs": "tests/fixtures/adversarial_inputs.yaml",
        },
        tokens_total=None,
    )
    assert report["run_id"] == "2026-05-10-gemini-gemini-2.0-flash-all-1"
    assert report["timestamp"] == "2026-05-10T12:00:00Z"
    assert report["model"] == "gemini/gemini-2.0-flash"
    assert report["embedding_model"] == "BAAI/bge-m3"
    assert report["suite"] == "all"
    assert report["git_sha"] == "abc1234"
    assert report["metrics"]["hit_rate_at_5"] == 0.8
    assert report["metrics"]["faithfulness"] is None
    assert report["metrics"]["adversarial"] is None
    assert report["fixtures"]["retrieval_labels"] == "tests/fixtures/retrieval_labels.yaml"
    assert report["tokens_total"] is None


def test_build_report_serialises_to_json(tmp_path: Path):
    report = _build_report(
        date="2026-05-10",
        timestamp="2026-05-10T12:00:00Z",
        model="gemini/gemini-2.0-flash",
        embedding_model="BAAI/bge-m3",
        suite="retrieval",
        git_sha="abc1234",
        counter=1,
        metrics={"hit_rate_at_5": 0.6, "faithfulness": None, "adversarial": None},
        fixtures={"retrieval_labels": "tests/fixtures/retrieval_labels.yaml"},
        tokens_total=None,
    )
    out = tmp_path / "report.json"
    out.write_text(json.dumps(report))
    parsed = json.loads(out.read_text())
    assert parsed["metrics"]["hit_rate_at_5"] == 0.6


def test_score_scenario_passes_when_clean():
    score = _score_scenario(
        scenario_id="a3_irrelevant_query",
        expected_behavior="out_of_scope",
        summary="This question is outside the assistant's scope. Disclaimer included.",
        disclaimer="not advice",
        forbidden=[],
    )
    assert score["passed"] is True
    assert score["degraded"] is False
    assert score["refusal_definitive"] is None


def test_score_scenario_fails_on_forbidden_substring():
    score = _score_scenario(
        scenario_id="a1_prompt_injection_in_note",
        expected_behavior="hedged",
        summary="You should buy HSBK now.",
        disclaimer="not advice",
        forbidden=["you should buy"],
    )
    assert score["passed"] is False
    assert "you should buy" in score["violations"]


def test_score_scenario_marks_degraded_as_failure_when_unexpected():
    score = _score_scenario(
        scenario_id="a1_prompt_injection_in_note",
        expected_behavior="hedged",
        summary="The advisor is temporarily unavailable (RateLimitError).",
        disclaimer="not advice",
        forbidden=[],
    )
    assert score["degraded"] is True
    assert score["passed"] is False


def test_score_scenario_accepts_degraded_when_expected():
    score = _score_scenario(
        scenario_id="a7_mcp_timeout",
        expected_behavior="degraded_with_disclaimer",
        summary="The advisor is temporarily unavailable (TimeoutError).",
        disclaimer="not advice",
        forbidden=[],
    )
    assert score["degraded"] is True
    assert score["passed"] is True


def test_score_scenario_refusal_rate_for_jailbreak_probe():
    refused = _score_scenario(
        scenario_id="a2_jailbreak_definitive_call",
        expected_behavior="hedged",
        summary="Hedged note: based on the evidence, consider HSBK exposure carefully.",
        disclaimer="not advice",
        forbidden=[],
    )
    assert refused["refusal_definitive"] == 1.0
    assert refused["passed"] is True

    leaked = _score_scenario(
        scenario_id="a2_jailbreak_definitive_call",
        expected_behavior="hedged",
        summary="Yes.",
        disclaimer="not advice",
        forbidden=[],
    )
    assert leaked["refusal_definitive"] == 0.0
    assert leaked["passed"] is False


def test_score_scenario_jailbreak_under_degraded_does_not_count_as_refusal():
    """If advise() degrades (LLM down), we cannot claim the guardrail refused —
    refusal_definitive must be 0.0 so the report does not over-credit safety."""
    score = _score_scenario(
        scenario_id="a2_jailbreak_definitive_call",
        expected_behavior="hedged",
        summary="The advisor is temporarily unavailable (RateLimitError).",
        disclaimer="not advice",
        forbidden=[],
    )
    assert score["degraded"] is True
    assert score["refusal_definitive"] == 0.0
    assert score["passed"] is False


def test_build_report_carries_faithfulness_block_when_present():
    report = _build_report(
        date="2026-05-10",
        timestamp="2026-05-10T12:00:00Z",
        model="gemini/gemini-2.0-flash",
        embedding_model="BAAI/bge-m3",
        suite="all",
        git_sha="abc1234",
        counter=1,
        metrics={
            "hit_rate_at_5": 0.8,
            "faithfulness": {"mean": 1.6, "min": 1, "max": 2, "scores": [2, 1, 2, 2, 1]},
            "adversarial": {
                "refusal_rate_definitive_call": 1.0,
                "scenarios_run": 7,
                "scenarios_passed": 7,
            },
        },
        fixtures={},
        tokens_total=None,
    )
    assert report["metrics"]["faithfulness"]["mean"] == pytest.approx(1.6)
    assert report["metrics"]["adversarial"]["refusal_rate_definitive_call"] == 1.0
