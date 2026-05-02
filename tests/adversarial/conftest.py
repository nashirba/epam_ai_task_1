# tests/adversarial/conftest.py
import os
import shutil
from pathlib import Path

import pytest


@pytest.fixture
def setup_adversarial(tmp_path: Path, monkeypatch, live_llm_required):
    """Stage adversarial fixtures from a scenario into a temp data dir; ingest into a separate Weaviate collection.

    Depends on live_llm_required so that the skip fires before the copytree runs.
    """
    src = Path("data")
    dst = tmp_path / "data"
    shutil.copytree(src, dst)
    monkeypatch.setenv("DATA_DIR", str(dst))
    yield dst


@pytest.fixture
def live_llm_required():
    if not os.getenv("PIA_LIVE_LLM"):
        pytest.skip("set PIA_LIVE_LLM=1 to run adversarial tests against a configured LLM")
