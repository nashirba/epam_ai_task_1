# ADR 0008: Embeddings Strategy — Provider Abstraction with Free Local Default

- **Status:** Accepted
- **Date:** 2026-05-02
- **Deciders:** Project owner

## Context

The RAG corpus is multilingual (RU + EN + some KZ). Retrieval quality is sensitive to embedding model choice, especially across languages. The owner asked for free-tier optionality alongside paid models. The grader should be able to run the system at $0.

## Decision

A thin `EmbeddingProvider` interface with three implementations, selected by env var `EMBEDDING_PROVIDER`:

- `openai` → OpenAI `text-embedding-3-small` (cheap paid baseline; LiteLLM-backed).
- `gemini` → Google `text-embedding-004` (free hosted; LiteLLM-backed).
- `local` → `BAAI/bge-m3` via `sentence-transformers` (multilingual, free, ~600MB on disk; default for the $0 path).

Embeddings used at ingest time are recorded as a property on each chunk (`embedding_model`); switching providers triggers a re-index, not silent skew. A small CLI command `python -m kz_rag.reindex` handles the swap.

Optional cross-encoder re-ranking pass (`BAAI/bge-reranker-base`) for top-20 → top-5, gated behind `RERANK=true` and added in the polish phase only if eval shows benefit.

## Consequences

**Positive**
- $0 grader path is real (local bge-m3 + free Gemini LLM).
- Multilingual quality benefits from a model designed for it.
- Provider abstraction reinforces the code-excellence narrative.

**Negative**
- Local embedding model adds ~600MB to the project image; mitigated by lazy-loading and a CDN-backed cache.
- First run downloads the model (~minutes); documented in README.
- Reindex is required on provider change.

**Neutral**
- Re-ranking is optional and may not ship in v1.

## Alternatives considered

- **OpenAI-only (no local fallback).** Rejected. Forfeits the $0 grader path.
- **Voyage / Cohere embeddings.** Considered; both are good but free tier limits make them awkward for a graded project where the reviewer may exhaust the quota.
- **Local-only (no hosted option).** Rejected. Some users (and the demo) prefer hosted speed; abstraction is cheap and useful.
- **Weaviate's built-in vectorizer module.** Rejected. Couples embeddings to the vector store and obscures the model used per chunk.

## Addendum (2026-05-05)

`LiteLLMEmbeddings.dim` raises `ValueError` for unknown model names rather than falling back to a default dimension. A silent dim fallback would corrupt the Weaviate index without surfacing the misconfiguration. Verified by `tests/unit/test_embeddings.py::test_litellm_embeddings_unknown_dimension_raises`.
