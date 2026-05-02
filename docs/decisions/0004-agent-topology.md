# ADR 0004: Agent Topology — 3 Agents, Orchestrator-Worker Pattern, In-Process Pydantic Bus

- **Status:** Accepted
- **Date:** 2026-05-02
- **Deciders:** Project owner

## Context

The brief requires "at least 3 agents with clearly defined, distinct roles and responsibilities" plus inter-agent communication. The instructor (Q&A meeting 1, lines ~105-120) acknowledges multiple inter-agent communication patterns and asks that the choice be deliberate and documented in the blueprint. Timeline is tight (16 days, 6 to draft).

## Decision

Three agents with clearly distinct responsibilities:

1. **Portfolio Agent** — answers questions about *what the user owns and what the user has written*. RAG over `data/personal/` and `data/public/`.
2. **Market Agent** — answers questions about *current market state*. MCP client to `kz-data` (custom) and a third-party web-search MCP.
3. **Planner / Advisor Agent** — user-facing orchestrator. Decomposes the query, calls the other two as needed, synthesizes a recommendation, attaches the compliance disclaimer.

**Inter-agent communication:** in-process function calls passing typed Pydantic message objects (`AgentMessage` with `request_id`, `sender`, `receiver`, `payload`). The Planner is the orchestrator; Portfolio and Market do not call each other.

## Consequences

**Positive**
- Clear, distinct roles satisfy the brief literally and substantively.
- Orchestrator-worker pattern is easy to test, easy to trace (single `request_id` joins all spans), easy to extend.
- In-process bus avoids deployment complexity of separate services for v1.
- Pydantic message types catch contract drift at runtime and serve as living documentation.

**Negative**
- The system does not demonstrate distributed agents. If a grader prefers HTTP-separated services, this looks "monolithic" — mitigated by clearly documenting the choice.
- Adding a fourth agent later requires updating the Planner orchestration logic.

**Neutral**
- A "swarm" pattern (no orchestrator) was considered. It's more impressive on paper but harder to debug and test; doesn't pay off in 16 days.

## Alternatives considered

- **4 agents (split out a News Agent).** Rejected. News fetching folds cleanly into the Planner via the web-search MCP because the Planner is already responsible for synthesis. A separate agent would add coordination cost without a distinct decision boundary.
- **5 agents (add a Compliance Agent).** Rejected. The compliance disclaimer is a deterministic Pydantic field on the response, not a model-driven decision; making it an agent would be theatre.
- **Swarm pattern (peer-to-peer agent communication, shared blackboard).** Rejected. Higher complexity, harder tests, no grading benefit at this timeline.
- **HTTP-microservice agents.** Rejected. Cost ≫ benefit for v1; container per agent is overkill when MCP already provides the cross-process boundary where it actually helps (data fetching).
- **File-based message passing (shared task list on disk).** Rejected. The instructor mentioned this as one valid pattern; it's clearer for distributed setups, but for an in-process system it's a net loss in observability.
