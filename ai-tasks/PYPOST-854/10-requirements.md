# PYPOST-854: Agent e2e docs/make follow-ups (verify absorption)

## Goals

Debt ticket from [PYPOST-839](https://pypost.atlassian.net/browse/PYPOST-839)
tracked three optional ergonomics items after the agent e2e packaging story:

1. Marker-based selection for agent e2e scenarios (TD-1)
2. Makefile smoke covering the focused agent e2e make target (TD-2)
3. Optional CI job/step that runs that make path alone (TD-3)

Sibling stories later owned those outcomes:

- [PYPOST-858](https://pypost.atlassian.net/browse/PYPOST-858) — Done —
  shared fixtures + registered `agent_e2e` marker (absorbs TD-1)
- [PYPOST-861](https://pypost.atlassian.net/browse/PYPOST-861) — Done —
  makefile smoke + dedicated CI `agent-e2e` job (absorbs TD-2, TD-3)

**Business goal for this task:** confirm the original debt outcomes are
already delivered for maintainers and agents (discoverable marker/make/CI
entry), document that 854 is superseded, and leave **no orphan follow-ups**
unless verification finds a real gap.

## Programming Language

No new product implementation expected. Verification uses the existing
Python/pytest/Makefile surface. Artifacts are Markdown
(`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **debt cleaner**, I want PYPOST-854 closed when TD-1–TD-3 are proven
  delivered elsewhere, so the sprint does not keep duplicate work.
- As a **scenario author / AI agent**, I want marker + `make test-agent-e2e`
  + CI gate to remain first-class so I do not invent one-off shell.
- As a **maintainer**, I want an honest closeout record if anything from
  839’s TD list is still missing.

## Definition of Done

- Each original TD item is mapped to a Done owner (858 and/or 861) **or**
  a residual gap is listed with NEW Debt.
- Verification evidence exists (marker registration, makefile smokes, CI
  job naming `make test-agent-e2e`).
- Top-down artifacts (roadmap + steps 1–7 files) honestly describe
  absorption / verify scope (not pretend new feature work).
- If nothing residual: **SAFE TO CLOSE** with no NEW Debt tickets.
- Out of band for this execution agent: commit and Jira Done transition
  (orchestrator / parent instructions).

## Task Description

**Problem:** PYPOST-854 still sits In Progress even though 858 and 861
already absorbed its TD items and documented make/CI/marker.

**Business need:** Close the loop so sprint accounting matches reality —
either residual smoke/docs, or an explicit superseded closeout.

### In Scope

- Verify TD-1 / TD-2 / TD-3 against repo + Done siblings.
- Write absorption-focused requirements, architecture (verify plan), and
  remaining workflow artifacts.
- List NEW Debt only for true residual gaps.

### Out of Scope

- Re-implementing marker, fixtures, makefile smoke, or CI job.
- Changing product UI or RequestWorker.
- User-facing product docs (`doc/user/`).
- Creating duplicate Jira Debt for items already ticketed under 858/861
  follow-ups (e.g. PYPOST-865–867, PYPOST-872–873).

## Constraints and Assumptions

- 858 and 861 are Done in Jira; their ai-tasks roadmaps are complete.
- Sprint-task-runner autonomous mode applies; user review gates waived.
- Parent run: do **not** commit; do **not** transition Jira.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Debt follow-up (854) | Tracks optional ergonomics from 839 |
| Marker outcome (TD-1) | Select agent e2e scenarios by name |
| Make smoke outcome (TD-2) | Guard recipe/help/deps for the target |
| CI gate outcome (TD-3) | Named pipeline path for the make target |
| Absorbing stories (858, 861) | Actual delivery owners |

## Q&A

- Q: Why not re-implement TD items under 854?
  A: Duplicate work; 858/861 AC already name absorption of 854.
- Q: What if verification finds a gap?
  A: Document residual + NEW Debt; do not close as superseded.
- Q: Is “verify only” a valid Step 3?
  A: Yes — DoD is proof of absorption, not new code when nothing remains.
