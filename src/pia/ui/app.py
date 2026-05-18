"""Streamlit entry: uv run streamlit run src/pia/ui/app.py"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import streamlit as st

from pia.agents.planner import advise
from pia.config import get_settings
from pia.ui.components import (
    citation_block,
    collect_snapshot_dates,
    diagnostics_view,
    disclaimer_banner,
    freshness_pill,
    portfolio_sidebar,
    render_history_citations,
)

st.set_page_config(page_title="Personal Investment Assistant", page_icon="💼", layout="wide")

# ---------------------------------------------------------------------------
# FX — live from kz-data MCP, with a constants fallback when MCP is down
# ---------------------------------------------------------------------------
_FX_FALLBACK: dict[str, float] = {"KZT": 1.0, "USD": 470.0, "EUR": 510.0}

# Substrings (case-insensitive) that indicate a degraded / error response.
# Shown as st.error with a "Try again" button instead of normal markdown.
_DEGRADED_MARKERS = (
    "temporarily unavailable",
    "temporarily rate-limiting",
    "Rate limit exceeded",
    "(no response",  # tool-call budget exhausted (BaseAgent.run sentinel)
    "ToolError",  # LLM may echo this from tool-role context; not a guaranteed signal
)


def _parse_fx(raw: object) -> float | None:
    """Best-effort extraction of a float from a kz-data get_fx_rate response.

    The MCP client returns result.content[0].text, which is a JSON string whose
    decoded form is {"pair": "KZT/USD", "rate": 470.0, "as_of": "...", "source": "..."}.
    """
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            try:
                return float(raw)
            except ValueError:
                return None
        return _parse_fx(data)
    if isinstance(raw, dict):
        # Primary key from pia/mcp/tools/fx.py return value
        if "rate" in raw and isinstance(raw["rate"], (int, float)):
            return float(raw["rate"])
        # Defensive extras in case the shape ever changes
        for key in ("value", "kzt_per_unit", "price"):
            if key in raw and isinstance(raw[key], (int, float)):
                return float(raw[key])
    return None


@st.cache_data(ttl=60)
def fetch_fx() -> tuple[dict[str, float], str | None]:
    """Live FX from kz-data MCP. Returns (fx_dict, fx_as_of_iso_date_or_None).

    fx_as_of is today's date if all requested rates came from MCP; None if any
    currency fell back to the constants in _FX_FALLBACK.
    """
    from pia.mcp.client import kz_data_call_sync  # imported here to avoid import-time side effects

    fx: dict[str, float] = dict(_FX_FALLBACK)
    all_live = True
    for pair, ccy in (("KZT/USD", "USD"), ("KZT/EUR", "EUR")):
        try:
            raw = kz_data_call_sync("get_fx_rate", pair=pair)
            value = _parse_fx(raw)
            if value is not None:
                fx[ccy] = value
            else:
                all_live = False
        except Exception:  # noqa: BLE001 - sidebar FX should fall back on any MCP failure
            all_live = False
    return fx, (date.today().isoformat() if all_live else None)


# ---------------------------------------------------------------------------
# Holdings loader
# ---------------------------------------------------------------------------


def _load_holdings() -> dict:
    p = Path(get_settings().data_dir) / "personal/holdings.json"
    return json.loads(p.read_text())


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

disclaimer_banner()
st.title("💼 Personal Investment-Planning Assistant")

with st.sidebar:
    holdings = _load_holdings()
    fx, fx_as_of = fetch_fx()

    # Freshness pill: holdings date + FX timestamp + public snapshot dates
    data_dir = Path(get_settings().data_dir)
    snapshot_dates = collect_snapshot_dates(data_dir)
    all_timestamps = {
        "holdings": holdings.get("as_of"),
        "fx": fx_as_of,  # None when fallback, ISO date when live
        **snapshot_dates,
    }
    freshness_pill(all_timestamps)
    if fx_as_of is None:
        st.caption("⚠️ FX rates: using fallback values (live MCP unavailable)")

    portfolio_sidebar(holdings, fx)
    diagnostics_view()

# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []  # list of dicts: {"role", "text", "citations", "sources"}

for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["text"])
        if msg.get("citations"):
            render_history_citations(msg["citations"])

if user_text := st.chat_input("Ask about your portfolio, the market, or what to do next…"):
    st.session_state.history.append({"role": "user", "text": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)
    with st.chat_message("assistant"):
        with st.status("Thinking…", expanded=True) as status:
            st.write("Sanitizing and routing input…")
            st.write("Calling Portfolio and Market agents…")
            rec = advise(user_text)
            st.write("Formatting answer…")
            status.update(label="Done", state="complete", expanded=False)
        if any(m.lower() in rec.summary.lower() for m in _DEGRADED_MARKERS):
            st.error(rec.summary, icon="⚠️")
            if st.button("Try again", key=f"retry_{len(st.session_state.history)}"):
                st.rerun()
        else:
            st.markdown(rec.summary)
            citation_block(rec)
        st.caption(rec.disclaimer)
    st.session_state.history.append(
        {
            "role": "assistant",
            "text": rec.summary,
            "citations": [c.model_dump() for c in rec.citations],
            "sources": [s.model_dump() for s in rec.market_sources],
        }
    )
