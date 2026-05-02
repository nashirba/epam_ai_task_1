``# ADR 0001: Use Architecture Decision Records

- **Status:** Accepted
- **Date:** 2026-05-02
- **Deciders:** Project owner (Nurlan), AI pair

## Context

The capstone requires an "Architecture Blueprint" deliverable, a self-review, an executive summary, and a video demo where decisions are explained verbally. Prior cohorts lost points when the rationale for design choices wasn't legible in the repo. The instructor explicitly recommended ADRs to keep AI-assisted development on a stable track and to document trade-offs (Q&A meeting 1, ~lines 65-72).

## Decision

We adopt Architecture Decision Records under `docs/decisions/`.

- File naming: `NNNN-kebab-title.md`, monotonically numbered.
- Each ADR includes: status, date, deciders, context, decision, consequences (positive / negative / neutral), and alternatives considered with reasoning for rejection.
- ADRs are written **at the time of the decision**, not retroactively.
- Superseding an ADR creates a new ADR that links back; the old one is marked `Superseded by NNNN`.
- The Architecture Blueprint deliverable summarizes accepted ADRs; the executive summary and video script reference them by number.

## Consequences

**Positive**
- Clear paper trail for graders, reviewers, and future-self.
- AI-assisted iterations stay aligned because the rationale is in the repo, not in chat history.
- Materials for the Architecture Blueprint and video voiceover assemble themselves.

**Negative**
- Slight overhead per decision (a few minutes to write).
- Risk of ADR sprawl if every micro-choice gets one — mitigated by writing ADRs only for non-trivial choices (frameworks, topology, data, security, evaluation, deployment).

**Neutral**
- ADRs do not replace the design spec; they are pinpoint records of *why a path was chosen*, while the spec describes *what is built*.

## Alternatives considered

- **Single decisions.md log** — rejected: harder to reference individually in deliverables, harder to see status transitions.
- **Comments in code only** — rejected: invisible to graders skimming the repo; degrades over time.
- **No formal record** — rejected: explicitly called out as a failure pattern by the instructor.
