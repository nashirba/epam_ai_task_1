"""Streamlit entry: uv run streamlit run src/pia/ui/app.py"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pandas as pd
import streamlit as st

from pia.agents.planner import advise
from pia.config import get_settings

st.set_page_config(page_title="Personal Investment Assistant", page_icon="💼", layout="wide")


def _to_kzt(pos: dict) -> float:
    fx = {"KZT": 1.0, "USD": 470.0, "EUR": 510.0}
    if "amount" in pos:
        return pos["amount"] * fx.get(pos["currency"], 1.0)
    return pos.get("shares", 0) * pos.get("avg_cost", 0) * fx.get(pos["currency"], 1.0)


def _load_holdings() -> dict:
    p = Path(get_settings().data_dir) / "personal/holdings.json"
    return json.loads(p.read_text())


def _allocation_df(holdings: dict) -> pd.DataFrame:
    by_class: dict[str, float] = defaultdict(float)
    for pos in holdings["positions"]:
        by_class[pos["asset_class"]] += _to_kzt(pos)
    return pd.DataFrame({"asset_class": list(by_class), "kzt": list(by_class.values())})


def _currency_df(holdings: dict) -> pd.DataFrame:
    by_ccy: dict[str, float] = defaultdict(float)
    for pos in holdings["positions"]:
        by_ccy[pos["currency"]] += _to_kzt(pos)
    return pd.DataFrame({"currency": list(by_ccy), "kzt": list(by_ccy.values())})


# --- top banner ---
st.warning(
    "Informational only. **Not** licensed financial, legal, or tax advice. "
    "Consult a licensed professional before acting.",
    icon="⚠️",
)

st.title("💼 Personal Investment-Planning Assistant")

with st.sidebar:
    st.header("Portfolio")
    holdings = _load_holdings()
    alloc = _allocation_df(holdings)
    ccy = _currency_df(holdings)
    st.caption(f"As of {holdings['as_of']}")
    st.dataframe(alloc, hide_index=True, use_container_width=True)
    st.subheader("By asset class")
    st.bar_chart(alloc, x="asset_class", y="kzt")
    st.subheader("By currency")
    st.bar_chart(ccy, x="currency", y="kzt")

# --- chat ---
if "history" not in st.session_state:
    st.session_state.history = []

for role, text in st.session_state.history:
    with st.chat_message(role):
        st.markdown(text)

if user_text := st.chat_input("Ask about your portfolio, the market, or what to do next…"):
    st.session_state.history.append(("user", user_text))
    with st.chat_message("user"):
        st.markdown(user_text)
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            rec = advise(user_text)
        st.markdown(rec.summary)
        st.caption(rec.disclaimer)
    st.session_state.history.append(("assistant", rec.summary))
