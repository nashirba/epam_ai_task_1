from __future__ import annotations

import json
from pathlib import Path


def get_nbk_rate(*, date_str: str | None = None, data_dir: Path) -> dict:
    """Return NBK base rate at `date_str` (or latest if None)."""
    history = json.loads((data_dir / "public/nbk/base_rate_history.json").read_text())["history"]
    history.sort(key=lambda r: r["effective_from"])
    pick = history[-1]
    if date_str:
        for entry in history:
            if entry["effective_from"] <= date_str:
                pick = entry
            else:
                break
    return {**pick, "as_of": date_str or pick["effective_from"], "source": "NBK base rate history"}
