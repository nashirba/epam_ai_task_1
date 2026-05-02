import os
import pytest
import yaml
from pathlib import Path

from pia.agents.planner import advise
from pia.eval.faithfulness import judge
from pia.rag.retrieve import retrieve


_LIVE = bool(os.getenv("PIA_LIVE_LLM"))
_GOLDEN = yaml.safe_load((Path(__file__).parent.parent / "fixtures" / "golden_qa.yaml").read_text())


@pytest.mark.skipif(not _LIVE, reason="set PIA_LIVE_LLM=1 to run faithfulness eval")
@pytest.mark.parametrize("case", _GOLDEN, ids=[c["id"] for c in _GOLDEN])
def test_faithfulness_above_threshold(case):
    rec = advise(case["question"])
    chunks = retrieve(case["question"], k=5)
    context = [f"[{c.source}] {c.text}" for c in chunks]
    result = judge(case["question"], context, rec.summary)
    assert result.score >= 1, f"{case['id']}: score={result.score}, rationale={result.rationale}"
