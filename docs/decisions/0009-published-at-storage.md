# ADR 0009: `published_at` Storage as DataType.TEXT in Weaviate

- **Status:** Accepted
- **Date:** 2026-05-02
- **Deciders:** Project owner (Nurlan), AI pair

## Context

`Citation.published_at` in `src/pia/messages.py` is a `str | None` ISO date
(e.g. `"2026-05-02"`).  The corresponding Weaviate property in
`src/pia/rag/store.py` is declared as `DataType.TEXT`:

```python
Property(name="published_at", data_type=DataType.TEXT),
```

News documents and `fx_history` snapshots carry publication dates that are
surfaced in the UI as citation chips (`"(published YYYY-MM-DD)"`).  Ideally,
these dates could also be used for server-side date-range filtering at
retrieval time — e.g. "give me news from the last week".

Weaviate provides a native `DataType.DATE` type that enables range queries
via `where: {operator: GreaterThan, valueDate: ...}`.  The question is whether
to use it for v1 or to keep the current TEXT storage.

## Decision

Keep `published_at` as `DataType.TEXT` in Weaviate for v1.  Do not convert to
`DataType.DATE`.

## Consequences

**Positive**
- No schema migration or re-ingest required.
- Missing or absent dates (loaders that do not provide `published_at`) are
  already handled as empty strings — no special-casing needed.
- ISO 8601 date strings sort lexicographically in the same order as
  chronological order (`"2026-05-02" < "2026-05-03"`), so naive string
  comparison remains correct for any in-Python ordering or filtering.

**Negative**
- Weaviate's native date-range filter (`where: {operator: GreaterThan,
  valueDate: ...}`) is unavailable because Weaviate rejects range comparisons
  on TEXT properties.
- Date filtering must happen as post-retrieval Python logic on the string
  value.  This is acceptable for v1 because the corpus is small (tens of
  documents; retrieval returns at most `k=5` results) and no date-range query
  is on the critical demo path.

**Neutral**
- Migration to `DataType.DATE` post-capstone is straightforward: re-create
  the collection with the updated schema and re-ingest.  The application
  contract (`Citation.published_at` as an ISO string) does not change.

## Alternatives considered

- **Convert to `DataType.DATE` now** — rejected for v1 because (a) several
  loaders mix sources where some lack publication dates, requiring special-case
  handling of `None` and empty strings at ingest time; (b) changing the schema
  forces a full re-ingest of the existing collection; (c) the demo's
  date-range retrieval needs are negligible — most user queries target
  "current" portfolio or market state, not historical date windows.

- **Add a parallel `published_at_unix` integer column** for numeric-range
  filtering — rejected as scope creep for v1; revisit if a concrete use case
  (e.g. a "last 7 days" filter in the UI) emerges post-capstone.

- **Drop the field entirely** — rejected: the UI citation chips display
  `"(published YYYY-MM-DD)"` for transparency; removing the field would
  degrade source auditability and likely lose rubric points.
