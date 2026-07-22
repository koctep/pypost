# PYPOST-880: Re-run full make check after harness timeout diagnostics

## Goals

Maintainers need confidence that the PYPOST-828 timeout-diagnostics harness
work (and its immediate siblings that shared the scoped gate) did not introduce
regressions outside the focused helper/consumer tests that already passed.
Re-running the full default quality gate restores that confidence without
changing product behavior.

## Programming Language

Python 3.10+

## User Stories

- As a **maintainer**, I want the full default quality gate to pass after the
  harness timeout-diagnostics work, so I know sibling suites are still green.
- As a **contributor**, I want any regression caused by that harness work fixed
  in a narrow way, so unrelated debt is not pulled into this ticket.
- As a **desktop user** (indirect), I want no change to product UX; this is a
  verification / quality-gate task only unless a harness regression must be
  fixed to clear the gate.

## Definition of Done

- Full `make check` has been run (or blockers that prevent a meaningful gate
  are documented with evidence).
- Any regressions attributable to PYPOST-828 harness timeout diagnostics are
  fixed; unrelated failures are not expanded into this ticket's scope.
- Focused diagnostic coverage from PYPOST-828 remains green.
- Task artifacts for Steps 1–8 exist under `ai-tasks/PYPOST-880/`.
- No intentional product behavior change beyond fixes required for harness
  regressions found by the gate.

## Task Description

**Problem:** PYPOST-828 was validated with `make lint` plus focused
helper/consumer tests (28 passed). Full `make check` was deferred as TD-3 when
sibling suite noise was a concern. That deferral is tracked as this Debt item.

**Business need:** Confirm no regressions outside the scoped gate so the
timeout-diagnostics harness can be trusted as part of the default quality
pipeline.

**Out of scope:** Unrelated flaky suites or pre-existing debt not caused by
PYPOST-828 harness work; wiring `worker_operation` (PYPOST-878); extracting
shared worker timeout helpers (PYPOST-879); product UX or storage format
changes.

**Source:** [PYPOST-880](https://pypost.atlassian.net/browse/PYPOST-880),
follow-up from [PYPOST-828](https://pypost.atlassian.net/browse/PYPOST-828)
TD-3 (`ai-tasks/PYPOST-828/60-tech-debt.md`).

## Constraints and Assumptions

- Verification / quality-gate task; prefer documenting N/A for a new red test
  unless the full gate surfaces a regression that needs a failing repro.
- Fix only regressions caused by PYPOST-828 harness work if found.
- If sibling suite noise still blocks a meaningful gate, document blockers
  rather than expanding into unrelated cleanup.

## Main Entities (business view)

- **Default quality gate** — full `make check` (lint + fast tests + ai-tasks
  verify).
- **Scoped gate** — lint + focused helper/consumer tests used for PYPOST-828.
- **Harness timeout diagnostics** — richer timeout detail from PYPOST-828.
- **Regression** — failure introduced by that harness work outside the scoped
  gate.

## Q&A

| Q | A |
| --- | --- |
| Why re-run full check? | Scoped gate cannot prove sibling suites stayed green. |
| Fix unrelated failures? | No — document and leave to their owners. |
| Product change? | Only if needed to clear a harness regression from 828. |
| Source debt item? | PYPOST-828 TD-3 → PYPOST-880. |
