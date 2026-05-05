"""Reusable Streamlit UI components for the Personal Investment Assistant."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from pia.messages import Recommendation
from pia.observability.metrics import get_registry


def diagnostics_view() -> None:
    """Show the in-process metrics registry in a sidebar expander.

    Counters: ``*.calls``, ``*.errors``, ``guardrail.*_fired``.
    Histograms: ``*.latency_s`` with p50 / p95 in milliseconds.
    Plus the last request id (Langfuse trace id) for cross-referencing the
    cloud dashboard. Empty until the first ``advise()`` call this process.
    """
    registry = get_registry()
    with st.expander("📊 Diagnostics", expanded=False):
        if registry.last_request_id:
            st.caption(f"Last trace id: `{registry.last_request_id}`")
        else:
            st.caption("No requests yet this session.")

        if registry.counters:
            counter_rows = sorted(
                ((c.name, c.value) for c in registry.counters.values()),
                key=lambda r: r[0],
            )
            st.write("**Counters**")
            st.dataframe(
                pd.DataFrame(counter_rows, columns=["metric", "value"]),
                hide_index=True,
                use_container_width=True,
            )

        if registry.histograms:
            latency_rows: list[tuple[str, int, float, float]] = []
            for hist in sorted(registry.histograms.values(), key=lambda h: h.name):
                p50 = hist.percentile(0.5)
                p95 = hist.percentile(0.95)
                if p50 is None or p95 is None:
                    continue
                latency_rows.append(
                    (hist.name, hist.count, round(p50 * 1000, 1), round(p95 * 1000, 1))
                )
            if latency_rows:
                st.write("**Latency (ms)**")
                st.dataframe(
                    pd.DataFrame(
                        latency_rows,
                        columns=["metric", "n", "p50", "p95"],
                    ),
                    hide_index=True,
                    use_container_width=True,
                )


def disclaimer_banner() -> None:
    """Render the top-of-page disclaimer warning."""
    st.warning(
        "Informational only. **Not** licensed financial, legal, or tax advice. "
        "Consult a licensed professional before acting.",
        icon="⚠️",
    )


def allocation_pie(df: pd.DataFrame, label_col: str, value_col: str, title: str) -> None:
    """Render an Altair donut chart (pie with hole) for the given DataFrame columns."""
    chart = (
        alt.Chart(df)
        .mark_arc(innerRadius=50)
        .encode(
            theta=alt.Theta(value_col, type="quantitative"),
            color=alt.Color(label_col, type="nominal"),
            tooltip=[label_col, value_col],
        )
        .properties(title=title, height=240)
    )
    st.altair_chart(chart, use_container_width=True)


def currency_pie(df: pd.DataFrame, label_col: str, value_col: str, title: str) -> None:
    """Render a donut chart for currency breakdown. Delegates to allocation_pie."""
    allocation_pie(df, label_col, value_col, title)


def portfolio_sidebar(holdings: dict, fx: dict[str, float]) -> None:
    """Render the portfolio sidebar: table, asset-class pie, and currency pie.

    Args:
        holdings: Loaded holdings.json as a dict.
        fx: FX rates keyed by currency code, e.g. {"KZT": 1.0, "USD": 470.0, "EUR": 510.0}.
    """

    def _to_kzt(pos: dict) -> float:
        if "amount" in pos:
            return pos["amount"] * fx.get(pos["currency"], 1.0)
        return pos.get("shares", 0) * pos.get("avg_cost", 0) * fx.get(pos["currency"], 1.0)

    by_class: dict[str, float] = defaultdict(float)
    by_ccy: dict[str, float] = defaultdict(float)
    for pos in holdings["positions"]:
        val = _to_kzt(pos)
        by_class[pos["asset_class"]] += val
        by_ccy[pos["currency"]] += val

    alloc = pd.DataFrame({"asset_class": list(by_class), "kzt": list(by_class.values())})
    ccy = pd.DataFrame({"currency": list(by_ccy), "kzt": list(by_ccy.values())})

    st.header("Portfolio")
    st.dataframe(alloc, hide_index=True, use_container_width=True)
    st.subheader("By asset class")
    allocation_pie(alloc, "asset_class", "kzt", "By asset class")
    st.subheader("By currency")
    currency_pie(ccy, "currency", "kzt", "By currency")


def citation_block(rec: Recommendation) -> None:
    """Render the Sources expander for a Recommendation. No-op if no citations."""
    if not rec.citations:
        return
    with st.expander(f"Sources ({len(rec.citations)})", expanded=True):
        for c in rec.citations:
            st.markdown(
                f"- **{c.source}** — `{c.source_url}` "
                + (f"_(published {c.published_at})_" if c.published_at else "")
            )
            if c.snippet:
                st.caption(c.snippet)


def render_history_citations(citations: list[dict]) -> None:
    """Render the citations block for a history message (dict-based, not model-based)."""
    if not citations:
        return
    with st.expander(f"Sources ({len(citations)})", expanded=False):
        for c in citations:
            st.markdown(
                f"- **{c['source']}** — `{c['source_url']}` "
                + (f"_(published {c['published_at']})_" if c.get("published_at") else "")
            )
            if c.get("snippet"):
                st.caption(c["snippet"])


def freshness_pill(timestamps: dict[str, str | None]) -> None:
    """Render a small 'Data as of …' caption summarising the freshest snapshot.

    Args:
        timestamps: Dict mapping source names to ISO-date strings (or None).
                    Example: {"holdings": "2026-05-02", "nbk": "2026-05-02"}.
    """
    valid = {k: v for k, v in timestamps.items() if v}
    if not valid:
        st.caption("📅 Data freshness unknown")
        return

    latest_key = max(valid, key=lambda k: valid[k])
    latest_date = valid[latest_key]
    oldest_key = min(valid, key=lambda k: valid[k])
    oldest_date = valid[oldest_key]

    if latest_date == oldest_date:
        st.caption(f"📅 Data as of {latest_date}")
    else:
        st.caption(f"📅 Data as of {latest_date} (oldest snapshot: {oldest_key} {oldest_date})")


def collect_snapshot_dates(data_dir: Path) -> dict[str, str | None]:
    """Scan public snapshot files and extract the most recent date per source.

    Returns a dict like {"nbk": "2026-05-02", "kase": "2026-05-02", "news": None}.
    """
    dates: dict[str, str | None] = {"nbk": None, "kase": None, "news": None}

    # NBK: read latest entry from fx_history.json
    fx_path = data_dir / "public/nbk/fx_history.json"
    if fx_path.exists():
        try:
            history = json.loads(fx_path.read_text()).get("history", [])
            if history:
                dates["nbk"] = max(e["date"] for e in history if "date" in e)
        except (json.JSONDecodeError, OSError, KeyError, ValueError):
            pass

    # KASE: filename pattern quotes-YYYY-MM-DD.json
    kase_dir = data_dir / "public/kase"
    if kase_dir.is_dir():
        kase_files = sorted(kase_dir.glob("quotes-*.json"))
        if kase_files:
            stem = kase_files[-1].stem  # e.g. "quotes-2026-05-02"
            dates["kase"] = stem.replace("quotes-", "")

    # News: .md files — use mtime or filename if it contains a date
    news_dir = data_dir / "public/news"
    if news_dir.is_dir():
        md_files = list(news_dir.glob("*.md"))
        if md_files:
            latest_mtime = max(f.stat().st_mtime for f in md_files)
            from datetime import datetime

            dates["news"] = datetime.fromtimestamp(latest_mtime).strftime("%Y-%m-%d")

    return dates
