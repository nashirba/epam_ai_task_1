# tests/integration/test_positive_qa.py
import os
import pytest
import yaml
from pathlib import Path

from pia.agents.planner import advise


_GOLDEN = yaml.safe_load(Path("tests/fixtures/golden_qa.yaml").read_text())
_LIVE = bool(os.getenv("PIA_LIVE_LLM"))


@pytest.mark.skipif(not _LIVE, reason="set PIA_LIVE_LLM=1 to run against a configured LLM")
@pytest.mark.parametrize("case", _GOLDEN, ids=[c["id"] for c in _GOLDEN])
def test_golden_qa(case):
    rec = advise(case["question"])
    text = rec.summary.lower()
    for sub in case["expected_substrings"]:
        assert sub.lower() in text, f"missing {sub!r} in: {rec.summary[:300]}"
    # tool-trace not currently propagated to Recommendation; assert at least one source recorded
    assert rec.citations or rec.market_sources, "no provenance recorded"
    assert rec.disclaimer
