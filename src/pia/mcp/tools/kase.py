from __future__ import annotations

import json
from pathlib import Path


def get_kase_quote(ticker: str, *, data_dir: Path) -> dict:
    """Return latest KASE snapshot for `ticker` across `data/public/kase/*.json`.

    Raises ValueError if the ticker is not found in any snapshot.
    """
    target = ticker.upper()
    snapshots = sorted((data_dir / "public/kase").glob("*.json"))
    if not snapshots:
        raise ValueError("No KASE snapshots found")

    best: dict | None = None
    best_date: str = ""
    for path in snapshots:
        if path.name == "PROVENANCE.md":
            continue
        try:
            doc = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        snapshot_date = doc.get("snapshot_date", "")
        # Skip files with no snapshot_date so as_of is never empty and ties are deterministic.
        if not snapshot_date:
            continue
        for row in doc.get("tickers", []):
            if row.get("ticker", "").upper() == target and (
                not best_date or snapshot_date > best_date
            ):
                best = row
                best_date = snapshot_date

    if best is None:
        raise ValueError(f"Unknown KASE ticker: {ticker!r}")

    return {
        "ticker": best["ticker"],
        "name": best.get("name"),
        "last": float(best["last"]),
        "change_pct_d": float(best.get("change_pct_d", 0.0)),
        "volume": int(best.get("volume", 0)),
        "currency": best.get("currency", "KZT"),
        "as_of": best_date,
        "source": "KASE",
    }
