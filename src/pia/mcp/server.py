"""kz-data MCP server.

Run: uv run python -m pia.mcp.server
"""

from __future__ import annotations

from pathlib import Path

from fastmcp import FastMCP

from pia.config import get_settings
from pia.mcp.tools.deposits import get_deposit_rates as _deposits
from pia.mcp.tools.fx import get_fx_rate as _fx
from pia.mcp.tools.kase import get_kase_quote as _kase
from pia.mcp.tools.nbk import get_nbk_rate as _nbk

_DATA = Path(get_settings().data_dir)
mcp = FastMCP("kz-data")


@mcp.tool()
def get_nbk_rate(date_str: str | None = None) -> dict:
    """NBK base rate at a date (ISO YYYY-MM-DD) or the latest entry.

    Returns rate_apr, effective_from, as_of.
    """
    return _nbk(date_str=date_str, data_dir=_DATA)


@mcp.tool()
def get_fx_rate(pair: str, date_str: str | None = None) -> dict:
    """FX spot or historical for pairs like 'KZT/USD', 'KZT/EUR', 'KZT/RUB'."""
    return _fx(pair, date_str=date_str, data_dir=_DATA)


@mcp.tool()
def get_kase_quote(ticker: str) -> dict:
    """Latest KASE snapshot for a ticker (HSBK, KCEL, ...)."""
    return _kase(ticker, data_dir=_DATA)


@mcp.tool()
def get_deposit_rates(currency: str, term_months: int) -> list[dict]:
    """Deposit rate sheet across banks for a currency and term."""
    return _deposits(currency, term_months, data_dir=_DATA)


if __name__ == "__main__":
    mcp.run()
