import pytest

from pia.embeddings import get_embedding_provider
from pia.embeddings.litellm import LiteLLMEmbeddings


@pytest.mark.integration
def test_local_provider_embeds(monkeypatch):
    class FakeSentenceTransformer:
        def __init__(self, model_name):
            self.model_name = model_name

        def get_sentence_embedding_dimension(self):
            return 3

        def encode(self, texts, **_kwargs):
            return [[1.0, 0.0, 0.0] for _ in texts]

    monkeypatch.setattr("pia.embeddings.local.SentenceTransformer", FakeSentenceTransformer)
    monkeypatch.setenv("EMBEDDING_PROVIDER", "local")
    monkeypatch.setenv("EMBEDDING_MODEL", "BAAI/bge-m3")
    provider = get_embedding_provider()
    vecs = provider.embed_batch(["hello world", "Halyk Bank deposit rate"])
    assert len(vecs) == 2
    assert len(vecs[0]) == provider.dim
    assert provider.dim > 0


def test_litellm_embeddings_unknown_dimension_raises():
    provider = LiteLLMEmbeddings(model="unknown/embedding-model")
    with pytest.raises(ValueError, match="Unknown embedding model dimension"):
        _ = provider.dim
