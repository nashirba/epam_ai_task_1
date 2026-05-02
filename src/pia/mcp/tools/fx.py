from __future__ import annotations

import json
from pathlib import Path

_PAIR_TO_KEY = {
    "KZT/USD": "kzt_per_usd",
    "KZT/EUR": "kzt_per_eur",
    "KZT/RUB": "kzt_per_rub",
}


def get_fx_rate(pair: str, *, date_str: str | None = None, data_dir: Path) -> dict:
    """Return FX rate for `pair` (e.g. 'KZT/USD') at `date_str` (or latest).

    Raises ValueError on unknown pair (only KZT/USD, KZT/EUR, KZT/RUB are supported).
    """
    key = _PAIR_TO_KEY.get(pair.upper())
    if key is None:
        raise ValueError(f"Unknown FX pair: {pair!r}. Supported: {sorted(_PAIR_TO_KEY)}")

    history = json.loads((data_dir / "public/nbk/fx_history.json").read_text())["history"]
    history.sort(key=lambda r: r["date"])
    pick = history[-1]
    if date_str:
        for entry in history:
            if entry["date"] <= date_str:
                pick = entry
            else:
                break
    return {
        "pair": pair.upper(),
        "rate": float(pick[key]),
        "as_of": pick["date"],
        "source": "NBK FX history",
    }
