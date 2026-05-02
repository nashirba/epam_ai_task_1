from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch, tmp_path: Path):
    """Default tests run with a clean env and an ephemeral DATA_DIR."""
    for k in [
        "LLM_MODEL",
        "EMBEDDING_PROVIDER",
        "WEAVIATE_HOST",
        "TAVILY_API_KEY",
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
    ]:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    (tmp_path / "data").mkdir()
    yield
