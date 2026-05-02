from __future__ import annotations

import json
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Document:
    # source values: 'user_note', 'user_holdings', 'user_plan', 'news',
    # 'bank_rates', 'kase', 'nbk', 'real_estate'
    source: str
    source_url: str  # path or URL
    text: str  # body to chunk and embed
    metadata: dict  # extra props (language, ticker, district, etc.)
    published_at: str | None = None
    language: str | None = None


_FRONT_MATTER = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


def _read_md(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8")
    m = _FRONT_MATTER.match(raw)
    if not m:
        return {}, raw
    meta = yaml.safe_load(m.group(1)) or {}
    return meta, m.group(2)


def _flatten_json(obj: object, prefix: str = "") -> str:
    """Render JSON as a deterministic text blob — good enough for hybrid search."""
    if isinstance(obj, dict):
        return "\n".join(f"{prefix}{k}: {_flatten_json(v, prefix)}" for k, v in obj.items())
    if isinstance(obj, list):
        return "\n".join(_flatten_json(x, prefix + "- ") for x in obj)
    return str(obj)


def load_documents(data_dir: Path) -> Iterator[Document]:
    # Personal notes
    for p in (data_dir / "personal/notes").glob("*.md"):
        meta, body = _read_md(p)
        yield Document(
            source="user_note",
            source_url=str(p),
            text=body,
            metadata=meta,
            published_at=meta.get("last_updated"),
            language=meta.get("language", "en"),
        )
    # Personal plan
    plan = data_dir / "personal/plan.md"
    if plan.exists():
        meta, body = _read_md(plan)
        yield Document("user_plan", str(plan), body, meta, meta.get("last_updated"), "en")
    # Personal holdings
    holdings = data_dir / "personal/holdings.json"
    if holdings.exists():
        obj = json.loads(holdings.read_text())
        yield Document(
            "user_holdings", str(holdings), _flatten_json(obj), obj, obj.get("as_of"), "en"
        )

    # News
    for p in (data_dir / "public/news").glob("*.md"):
        meta, body = _read_md(p)
        yield Document(
            "news",
            meta.get("url", str(p)),
            body,
            meta,
            meta.get("published"),
            meta.get("language", "ru"),
        )

    # Bank rates
    for p in (data_dir / "public/bank_rates").glob("*.json"):
        obj = json.loads(p.read_text())
        yield Document(
            "bank_rates",
            obj.get("source_url", str(p)),
            _flatten_json(obj),
            obj,
            obj.get("snapshot_date"),
            "en",
        )

    # KASE / NBK / Krisha
    for sub, src in [
        ("public/kase", "kase"),
        ("public/nbk", "nbk"),
        ("public/real_estate/almaty", "real_estate"),
    ]:
        for p in (data_dir / sub).glob("*.json"):
            obj = json.loads(p.read_text())
            yield Document(
                src,
                obj.get("source_url", str(p)),
                _flatten_json(obj),
                obj,
                obj.get("snapshot_date"),
                "en",
            )
