# Resume prompt — start post-draft Phase 7

> Paste everything inside the `<prompt>…</prompt>` block (without the tags) into a fresh Claude Code session in `/Users/nashirba/epam_course/task_1`. The prompt is self-contained — the next session doesn't need any chat history.

<prompt>

I'm Nurlan, EPAM email `nurlan@stellarcard.io`. I'm working on my EPAM Generative AI Engineering capstone project — a **Personal Investment-Planning Assistant for a Kazakhstan-resident individual investor** (multi-agent RAG + MCP). Submission deadline is **Sun 2026-05-18**. I plan to send a draft to the committee around Fri 2026-05-08.

The pre-draft milestone is complete and tagged `v0.1.0-draft`. You're picking up at **Phase 7 of the post-draft plan**.

## Working directory and branch

`/Users/nashirba/epam_course/task_1` on branch `feature/capstone_project`. Do NOT push, do NOT change branches, do NOT do anything destructive without asking me first.

## Pre-flight — verify state before starting

Run these and confirm they match. If any don't, STOP and tell me — something changed since the previous session.

```bash
git -C /Users/nashirba/epam_course/task_1 log --oneline -3
# Expected (top three):
#   69ca708 Add post-draft implementation plan (Days 8-16)
#   f291316 Phase 6: README quickstart polish + draft-issues punch list
#   89c1b2b Phase 5: Streamlit UI ...

git -C /Users/nashirba/epam_course/task_1 tag --list | grep v0.1.0-draft   # should print "v0.1.0-draft"
git -C /Users/nashirba/epam_course/task_1 status                           # should be clean
cd /Users/nashirba/epam_course/task_1 && uv run pytest tests/unit -v       # 13/13 should pass
```

## Canonical references — read these BEFORE you do anything

If the plan and the spec/ADRs disagree, **the spec/ADRs win**. The user (me) hand-edits the spec/ADRs sometimes; treat them as source of truth.

- Spec: `docs/superpowers/specs/2026-05-02-personal-investment-assistant-design.md`
- ADRs: `docs/decisions/0001-…` through `0008-…`
- Requirements addendum (meeting-derived constraints): `docs/requirements_addendum.md`
- **Pre-draft plan (already executed)**: `docs/superpowers/plans/2026-05-02-pia-pre-draft.md`
- **Post-draft plan (you execute this)**: `docs/superpowers/plans/2026-05-02-pia-post-draft.md`
- Punch list / deferred items: `docs/draft-issues.md`
- Original brief / NFRs / success criteria: `docs/brief.md`, `docs/non_functional_requirements.md`, `docs/success_criteria.md`
- Stakeholder Q&A meeting notes (binding): `docs/meetings/q_a_meetings_1.text`, `q_a_meetings_2.text`

## Workflow rules (durable preferences)

1. Use **superpowers:subagent-driven-development** — fresh subagent per phase, two-stage review (spec compliance → code quality), then a fixer subagent if issues are found. Phases 0-6 in the pre-draft followed this; continue it.
2. **Document every meaningful technical decision as an ADR** under `docs/decisions/NNNN-kebab-title.md`. The post-draft plan already specifies ADRs 0009 (`published_at` storage), 0010 (Langfuse observability), 0011 (safety layered facade), 0012 (eval harness). Write each ADR at the moment of the decision, not retroactively. The convention is locked in by ADR 0001.
3. Stay on `feature/capstone_project`. Do NOT push, do NOT use `--no-verify`, do NOT `git reset --hard` or similar without explicit approval.
4. Use Sonnet 4.6 unless I tell you otherwise.
5. When a subagent finishes a phase, present commit SHA + a short summary and ask before continuing to the next phase. Don't auto-chain phases.

## Your task this session

Execute **Phase 7** of `docs/superpowers/plans/2026-05-02-pia-post-draft.md` (the section starting with `## Phase 7 — Day 8`). Phase 7 contains tasks 7.1 through 7.7:

- 7.1 Citations through to UI (final-review Important #1, #2, #3, #5)
- 7.2 BaseAgent loop unit tests
- 7.3 `advise()` always-returns-Recommendation test
- 7.4 Tool-schema `additionalProperties: false` everywhere
- 7.5 Golden Q&A positive test fixture + integration test (live-LLM gated)
- 7.6 Retrieval@k metric + threshold test
- 7.7 Single Phase 7 commit + tag `v0.1.1-fixes`

End state: all unit tests still pass (the new ones included), retrieval@5 ≥ 0.6 against the labeled set, the golden Q&A test runs cleanly when `PIA_LIVE_LLM=1` is set (it'll skip otherwise), the UI now renders a "Sources" expander on every assistant message.

After Phase 7 is committed, reviewed (spec compliance + code quality), and tagged: stop and ask me whether to continue with Phase 8 (adversarial tests) or pause. **Do not auto-continue past Phase 7.**

## Things I may do separately — don't trigger these

- Push the draft tag: `git push origin feature/capstone_project && git push origin v0.1.0-draft`
- Run the live smoke (5 representative queries) with a real LLM key
- Send the draft to the committee

## How to start

1. Read the pre-flight checks output and confirm state.
2. Read the post-draft plan's Phase 7 section.
3. Invoke `superpowers:subagent-driven-development`.
4. Dispatch a Phase 7 implementer subagent with the full Phase 7 text (don't make the subagent re-read the file — paste the section into its prompt).
5. After implementer DONE → dispatch spec compliance reviewer.
6. If spec ✅ → dispatch code quality reviewer.
7. If issues → fixer subagent.
8. Mark Phase 7 done; report back to me; await my next instruction.

Begin.

</prompt>

## How to use

1. Open a fresh Claude Code session at `/Users/nashirba/epam_course/task_1` (`claude` in the terminal).
2. Copy the text inside the `<prompt>…</prompt>` block above.
3. Paste it as your first message.

The new session will have zero context from this conversation, but the prompt is self-contained: it tells the agent which docs are canonical, what state to verify, what workflow to follow, and what to execute. The agent will pick up at Phase 7 with the same subagent-driven-development discipline.

If the new session's pre-flight checks fail, the agent will stop and tell you — that protects against drift between sessions.
