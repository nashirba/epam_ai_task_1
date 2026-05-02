from pia.config import Settings


def test_settings_loads_defaults(monkeypatch):
    monkeypatch.delenv("LLM_MODEL", raising=False)
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.llm_model == "gemini/gemini-2.0-flash"
    assert s.embedding_provider == "local"
    assert s.weaviate_http_port == 8080
    assert s.rate_limit_per_minute == 10


def test_settings_respects_env(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "anthropic/claude-sonnet-4-6")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.llm_model == "anthropic/claude-sonnet-4-6"
    assert s.embedding_provider == "openai"
