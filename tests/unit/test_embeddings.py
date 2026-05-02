import pytest

from pia.embeddings import get_embedding_provider


@pytest.mark.integration
def test_local_provider_embeds(monkeypatch):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "local")
    monkeypatch.setenv("EMBEDDING_MODEL", "BAAI/bge-m3")
    provider = get_embedding_provider()
    vecs = provider.embed_batch(["hello world", "Halyk Bank deposit rate"])
    assert len(vecs) == 2
    assert len(vecs[0]) == provider.dim
    assert provider.dim > 0
