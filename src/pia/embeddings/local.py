from __future__ import annotations

from functools import cached_property

from sentence_transformers import SentenceTransformer


class LocalEmbeddings:
    def __init__(self, model_name: str = "BAAI/bge-m3") -> None:
        self._model_name = model_name

    @cached_property
    def _model(self) -> SentenceTransformer:
        return SentenceTransformer(self._model_name)

    @property
    def name(self) -> str:
        return f"local:{self._model_name}"

    @property
    def dim(self) -> int:
        return int(self._model.get_sentence_embedding_dimension())

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        embs = self._model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=4,
        )
        return [list(map(float, v)) for v in embs]

    def embed_one(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]
