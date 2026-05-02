from pia.config import get_settings
from pia.embeddings.base import EmbeddingProvider
from pia.embeddings.litellm import LiteLLMEmbeddings
from pia.embeddings.local import LocalEmbeddings


def get_embedding_provider() -> EmbeddingProvider:
    s = get_settings()
    if s.embedding_provider == "local":
        return LocalEmbeddings(model_name=s.embedding_model)
    if s.embedding_provider == "openai":
        return LiteLLMEmbeddings(model="text-embedding-3-small")
    if s.embedding_provider == "gemini":
        return LiteLLMEmbeddings(model="gemini/text-embedding-004")
    raise ValueError(f"unknown EMBEDDING_PROVIDER: {s.embedding_provider}")
