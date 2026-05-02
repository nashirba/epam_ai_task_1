from __future__ import annotations

import litellm

_MODEL_DIMS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "gemini/text-embedding-004": 768,
}


class LiteLLMEmbeddings:
    def __init__(self, model: str) -> None:
        self._model = model

    @property
    def name(self) -> str:
        return f"litellm:{self._model}"

    @property
    def dim(self) -> int:
        return _MODEL_DIMS.get(self._model, 1536)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        resp = litellm.embedding(model=self._model, input=texts)
        return [d["embedding"] for d in resp["data"]]

    def embed_one(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]
