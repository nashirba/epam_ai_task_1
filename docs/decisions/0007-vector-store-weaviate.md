# ADR 0007: Vector Store — Self-Hosted Weaviate via Docker Compose

- **Status:** Accepted
- **Date:** 2026-05-02
- **Deciders:** Project owner

## Context

The RAG pipeline retrieves over a multilingual corpus (RU + EN + some KZ) of news, filings, bank rate sheets, listings, and personal notes. Hybrid search (BM25 + vector) materially improves retrieval quality on multilingual + entity-heavy content (e.g., ticker symbols, bank names) compared with pure dense retrieval. The "deployable product" requirement favors a self-hostable store with a clean Docker story.

## Decision

Use **Weaviate** self-hosted via `docker-compose.yml`. One single-node instance with a persistent volume.

- One collection per source type (`Filings`, `News`, `BankRates`, `Listings`, `KASE`, `NBK`, `UserNotes`, `UserHoldings`).
- Common properties on every collection: `content`, `source`, `source_url`, `published_at`, `language`, `tags[]`.
- Hybrid search (`alpha=0.5` to start, tunable per-collection if eval shows benefit).
- Vectorization done by our embedding provider (ADR 0008), not Weaviate's built-in vectorizer modules — keeps embeddings under our control and consistent across collections.

## Consequences

**Positive**
- Out-of-the-box hybrid search (BM25 + dense) without a second store.
- Multilingual-friendly with appropriate embeddings (e.g., bge-m3).
- Clear `docker compose up` story → satisfies "deployable product."
- Supports cross-references and metadata filters out of the box, enabling clean source attribution and language/asset-class filtering.
- Mature Python v4 client.

**Negative**
- Heavier than Chroma for a small corpus — but our corpus is intentionally not toy-scale.
- One more container in the compose file; docs must explain `docker compose down` between sessions.

**Neutral**
- Weaviate Cloud sandbox was available but expires; self-hosted via Docker is more honest to the "deployable product" framing.

## Alternatives considered

- **ChromaDB.** Rejected. No native hybrid search; multilingual story weaker; dense-only retrieval underperforms on entity-heavy KZ content.
- **pgvector (Postgres).** Rejected. Hybrid search must be hand-wired; tooling is heavier than Weaviate's first-class hybrid.
- **Qdrant.** Acceptable backup with hybrid search. Weaviate edges it on Python ergonomics and cross-references.
- **FAISS in-process.** Rejected. No persistence story; reviewer experience is poor.
- **In-memory only.** Rejected. Reload time on every dev run kills iteration speed.
