# tests/unit/test_smoke.py
import importlib


def test_pia_imports():
    pia = importlib.import_module("pia")
    assert pia is not None


def test_settings_constructs():
    from pia.config import get_settings
    s = get_settings()
    assert s.llm_model
    assert s.weaviate_http_port == 8080
