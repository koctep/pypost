# PYPOST-882: Full make check after gateway H3 finish-path fix

## Goals

Maintainers need confidence that the PYPOST-829 storage-gateway H3
finish-path fix (and the stress canary that proved it) did not introduce
regressions outside the focused gateway / responsiveness / H3 isolation
that already passed. Re-running the full default quality gate restores
that confidence without changing product behavior.

## Programming Language

Python 3.10+

## User Stories

- As a **maintainer**, I want the full default quality gate to pass after
  the H3 finish-path work, so I know sibling suites are still green.
- As a **contributor**, I want any regression caused by that finish-path
  work fixed in a narrow way, so unrelated debt is not pulled into this
  ticket.
- As a **desktop user** (indirect), I want no change to product UX; this
  is a verification / quality-gate task only unless a finish-path
  regression must be fixed to clear the gate.

## Definition of Done

- Full `make check` has been run (or blockers that prevent a meaningful
  gate are documented with evidence).
- Any regressions attributable to the PYPOST-829 H3 finish-path fix are
  fixed; unrelated failures are not expanded into this ticket's scope.
- Focused gateway + responsiveness + H3 stress isolation from PYPOST-829
  remains green.
- Task artifacts for Steps 1–8 exist under `ai-tasks/PYPOST-882/`.
- No intentional product behavior change beyond fixes required for
  PYPOST-829 regressions found by the gate.

## Task Description

**Problem:** PYPOST-829 was validated with `make lint` plus focused
gateway + responsiveness + H3 stress isolation (20 passed). Full
`make check` was deferred as TD-2 when sibling suite noise was a concern.
That deferral is tracked as this Debt item.

**Business need:** Confirm no regressions outside the scoped gate so the
H3 finish-path hygiene can be trusted as part of the default quality
pipeline.

**Out of scope:** Unrelated flaky suites or pre-existing debt not caused
by PYPOST-829 finish-path work; shared finish-teardown helper
(PYPOST-881); shared `qapp` / suite affinity (PYPOST-830); product UX or
storage format changes.

**Source:** [PYPOST-882](https://pypost.atlassian.net/browse/PYPOST-882),
follow-up from [PYPOST-829](https://pypost.atlassian.net/browse/PYPOST-829)
TD-2 (`ai-tasks/PYPOST-829/60-tech-debt.md`).

## Constraints and Assumptions

- Verification / quality-gate task; prefer documenting N/A for a new red
  test unless the full gate surfaces a regression that needs a failing
  repro.
- Fix only regressions caused by PYPOST-829 H3 finish-path work if found.
- If sibling suite noise still blocks a meaningful gate, document
  blockers rather than expanding into unrelated cleanup.
- Sibling note (PYPOST-880): plain `make check` can stall on
  `save_async` nested Qt; prefer `make lint` + `make test` with
  `--timeout-method=thread` when needed, and document evidence.

## Main Entities (business view)

- **Default quality gate** — full `make check` (lint + fast tests +
  ai-tasks verify).
- **Scoped gate** — lint + focused gateway / responsiveness / H3 stress
  used for PYPOST-829.
- **H3 finish-path fix** — worker finish teardown with ordered
  teardown before pending restart (both storage gateways).
- **Regression** — failure introduced by that finish-path work outside
  the scoped gate.

## Q&A

| Q | A |
| --- | --- |
| Why re-run full check? | Scoped gate cannot prove sibling suites stayed green. |
| Fix unrelated failures? | No — document and leave to their owners. |
| Product change? | Only if needed to clear a finish-path regression from 829. |
| Source debt item? | PYPOST-829 TD-2 → PYPOST-882. |
| Plain check stalls? | Document; use thread timeout method if needed (PYPOST-880). |
