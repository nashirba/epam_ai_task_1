from datetime import date
from pathlib import Path

from pia.mcp.tools.deposits import get_deposit_rates
from pia.mcp.tools.fx import get_fx_rate
from pia.mcp.tools.kase import get_kase_quote
from pia.mcp.tools.nbk import get_nbk_rate


def test_nbk_rate_latest(tmp_path):
    base = Path("data")
    out = get_nbk_rate(date_str=None, data_dir=base)
    assert "rate_apr" in out
    assert out["effective_from"] <= date.today().isoformat()


def test_fx_rate_pair(tmp_path):
    out = get_fx_rate("KZT/USD", data_dir=Path("data"))
    assert out["pair"] == "KZT/USD"
    assert out["rate"] > 0


def test_kase_quote_known_ticker():
    out = get_kase_quote("HSBK", data_dir=Path("data"))
    assert out["ticker"] == "HSBK"
    assert out["last"] > 0


def test_deposit_rates_kzt_12m():
    out = get_deposit_rates("KZT", 12, data_dir=Path("data"))
    assert isinstance(out, list)
    assert all(p["currency"] == "KZT" for p in out)
