# ADR 0002: Domain and Scope — Personal Investment-Planning Assistant for KZ-Resident Investor

- **Status:** Accepted
- **Date:** 2026-05-02
- **Deciders:** Project owner

## Context

The brief mandates "Personal Knowledge Assistant" with multi-agent RAG + MCP. Within that frame, the topic must be a real-world problem with a substantive corpus and a defensible investor-pitch story. The project owner is a KZ-resident software developer with idle capital, no time to track markets, and concrete pain around bank-deposit decisions, real-estate exposure (Almaty), KZ equities (KASE), and currency exposure.

## Decision

The capstone domain is a **personal investment-planning assistant for a Kazakhstan-resident individual investor**. The system answers three jobs: (1) track current holdings, (2) monitor markets and news that affect those holdings, (3) recommend allocation changes with citations and a compliance disclaimer.

**v1 asset classes:** KZT/USD bank deposits, residential real estate (Almaty), KASE-listed equities, US ETFs.

**v1 capabilities:** holdings tracking, allocation analysis (by asset class and by currency), news relevance to holdings, recommendation generation with disclaimer.

**Explicit non-goals (v1):** crypto, gold, UAPF, AIX bonds, mutual funds; brokerage execution; multi-user; live data refresh; multilingual UI.

## Consequences

**Positive**
- Authentic, defensible demo (option E from brainstorming — owner has skin in the game).
- Free, real, multi-source data corpus (NBK, KASE, Krisha, bank rate sheets, KZ news).
- Multilingual content (RU + EN + some KZ) drives a stronger embeddings/retrieval narrative.
- Adversarial tests are natural and meaningful (jailbreaks asking for buy/sell calls, conflicting bank rates, prompt-injected notes).

**Negative**
- KZ-specific data sources have weaker public APIs; some scraping is required.
- Compliance/ethics burden is real — must include disclaimers and refuse definitive advice.

**Neutral**
- Future scope expansions (crypto, gold, UAPF, AIX) are obvious and can be discussed in the executive summary as "next steps."

## Alternatives considered

- **US-only equity research** — rejected: weaker user fit and no personal stakes; would feel academic.
- **Personal medical assistant** — rejected: PII burden too heavy for the timeline.
- **Developer "second brain"** — rejected: weakest investor-pitch story; data quality bonus harder to defend.
- **Full asset coverage on day 1 (incl. crypto, gold, UAPF, mutual funds, AIX)** — rejected: timeline doesn't allow it for v1; deferred to "next steps."
