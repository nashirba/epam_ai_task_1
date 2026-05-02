from __future__ import annotations

import json
from pathlib import Path


def get_deposit_rates(currency: str, term_months: int, *, data_dir: Path) -> list[dict]:
    """Return matching deposit products across banks, sorted by APR (best first)."""
    target_currency = currency.upper()
    results: list[dict] = []

    for path in sorted((data_dir / "public/bank_rates").glob("*.json")):
        if path.name == "PROVENANCE.md":
            continue
        try:
            doc = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        bank = doc.get("bank", path.stem)
        snapshot_date = doc.get("snapshot_date", "")
        source_url = doc.get("source_url", "")
        for product in doc.get("products", []):
            if product.get("currency", "").upper() == target_currency and int(
                product.get("term_months", -1)
            ) == int(term_months):
                results.append(
                    {
                        "bank": bank,
                        "name": product.get("name", ""),
                        "currency": target_currency,
                        "term_months": int(term_months),
                        "rate_apr": float(product.get("rate_apr", 0.0)),
                        "min_amount": float(product.get("min_amount", 0)),
                        "as_of": snapshot_date,
                        "source_url": source_url,
                    }
                )

    results.sort(key=lambda r: r["rate_apr"], reverse=True)
    return results
