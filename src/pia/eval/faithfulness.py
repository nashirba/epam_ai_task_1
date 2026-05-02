"""LLM-as-judge: given an answer and the chunks the system retrieved, decide whether the
answer is grounded in those chunks. Returns a (score, rationale) per case.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from pia.llm.client import LLMClient


_JUDGE_SYSTEM = """You are a strict evaluator. Given:

(1) a question,
(2) a set of retrieved context chunks (with sources),
(3) an answer the system produced,

decide whether the answer's factual claims are supported by the context. Output strict JSON:

{"score": 0|1|2, "rationale": "..."}

Where: 0 = not grounded (hallucinates or contradicts), 1 = partially grounded, 2 = fully grounded.
"""


@dataclass
class JudgeResult:
    score: int
    rationale: str


def judge(question: str, context: list[str], answer: str, *, llm: LLMClient | None = None) -> JudgeResult:
    llm = llm or LLMClient()
    user = f"Question:\n{question}\n\nContext:\n" + "\n---\n".join(context) + f"\n\nAnswer:\n{answer}\n"
    out = llm.chat([
        {"role": "system", "content": _JUDGE_SYSTEM},
        {"role": "user", "content": user},
    ])
    try:
        parsed = json.loads(out["content"])
        return JudgeResult(score=int(parsed["score"]), rationale=str(parsed["rationale"]))
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        return JudgeResult(score=0, rationale=f"judge output unparseable: {exc}; raw: {out['content'][:200]}")
