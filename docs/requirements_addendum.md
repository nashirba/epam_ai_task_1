# Requirements Addendum

This document supplements `brief.md`, `non_functional_requirements.md`, and `success_criteria.md` with constraints and clarifications surfaced in the Q&A meetings (`docs/meetings/q_a_meetings_1.text`, `q_a_meetings_2.text`). These are binding for the capstone submission and must be honored alongside the original requirements.

## A. Ownership and deployment

1. **Own code for core agentic logic.** All agent orchestration, inter-agent communication, and MCP wiring must be implemented in our own codebase. Third-party orchestration platforms (e.g., n8n, Make, Flowise, Dify, LangGraph Cloud) are not acceptable for the core multi-agent logic. Frameworks used as libraries (LangChain, LlamaIndex, LangGraph as a library, CrewAI, etc.) are acceptable.
2. **Deployable product, not a notebook.** The system must run as a real application — local process, Docker, or cloud deployment. Jupyter/Colab notebooks are not an acceptable delivery shape (notebooks may exist as scratch/experiments but not as the product).
3. **External services are allowed for non-core dependencies.** Hosted LLMs, vector databases, and similar managed components are fine. The agentic and MCP code must be ours.

> Source: `q_a_meetings_2.text`, lines ~19-49.

## B. Quality bar — MVP+, not PoC

4. The submission must reach **MVP+**: a complete, defensible product, not a hypothesis-checking proof of concept with gaps.
5. The video demo must show end-to-end flow plus tests (positive and adversarial). No silent video. No notebook walkthrough as the demo.

> Source: `q_a_meetings_2.text`, lines ~74-80; `q_a_meetings_1.text`, lines ~134-138.

## C. Data quality bar

6. The RAG corpus must be **realistic in scale and content** — for a single-domain assistant, target dozens of real documents (≈20-50+ realistic items), not 3-5 mock entries. Toy data forfeits the +10 Data Quality bonus and weakens demo argumentation.
7. Data preparation, cleaning, and validation steps must be visible in the repo (scripts or notebooks under a clearly named directory, plus a short README explaining provenance and licenses).

> Source: `q_a_meetings_2.text`, lines ~58-69.

## D. Topic submission and validation

8. The capstone topic must be submitted to the committee with a description containing: the real-world problem, the ≥3 agents and their roles, the purpose and target of RAG, and the role of MCP. Work is not formally "started" until the committee accepts the topic.

> Source: `q_a_meetings_2.text`, lines ~1-10.

## E. Architecture and process

9. **ADRs are mandatory.** Every meaningful technical decision (framework, agent topology, retrieval strategy, MCP target, prompt-injection defense, eval approach, deployment shape, UI stack, etc.) is captured as a numbered ADR under `docs/decisions/`. ADRs feed the Architecture Blueprint deliverable and the demo voiceover.
10. **Inter-agent communication is a deliberate choice.** The blueprint must explicitly justify the chosen pattern (network/MCP messaging vs. shared filesystem/task queue vs. orchestrated function calls).

> Source: `q_a_meetings_1.text`, lines ~65-72, ~105-120.

## F. Submission pitfalls to avoid

11. The most common reasons for rework on prior cohorts:
    - Missing video, or video without a voiceover.
    - Executive summary that doesn't follow the 1-2 page exec-summary format (problem → key technical choices → results & business value → next steps), aimed at non-technical reviewers.
    - Missing one of the seven required deliverables in the repo: Executive Summary, Architecture Blueprint, README, Code, Test Suite, Self-Review, Video Demo link.
12. The submission file must be a plain text file named `Capstone_project_<First>_<Last>.txt` containing the EPAM email, repo link, and video link — nothing else mandatory.

> Source: `q_a_meetings_1.text`, lines ~80-93, ~134-138; `step_by_step_implementation_guide.md`.

## G. Testing scope

13. The test suite must cover both **positive** (happy-path agent flows, retrieval correctness on known queries, MCP success cases) and **negative/adversarial** (prompt injection, jailbreaks, irrelevant queries, retrieval misses, MCP timeouts/errors, PII leakage) scenarios. Adversarial tests are weighted in grading; they cannot be skipped.

> Source: `brief.md` ("positive and negative test scenarios"); `success_criteria.md`.

## H. Compliance, safety, and observability

14. The non-functional requirements in `non_functional_requirements.md` are not aspirational — observability (LLM tracing, metrics, errors), safety (input validation, content filtering, PII detection), RAG QA (retrieval precision/recall, hallucination flagging, source attribution), cost (local-first where reasonable, free-tier compliance), and graceful degradation must each have at least one demonstrable implementation in the codebase and at least one test or dashboard view.

> Source: `non_functional_requirements.md`; reinforced as "must be satisfied" in `q_a_meetings_1.text`, lines ~26-28.
