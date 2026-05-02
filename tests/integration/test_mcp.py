import pytest

from pia.mcp.client import kz_data_call_sync


@pytest.mark.integration
def test_kz_data_nbk_via_mcp():
    out = kz_data_call_sync("get_nbk_rate")
    assert out is not None
