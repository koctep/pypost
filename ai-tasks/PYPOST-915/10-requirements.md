# PYPOST-915: Dedicated OSError / AttributeError dump best-effort units

## Goals

Lock the agent e2e failure dump helper’s best-effort contract for `OSError`
(disk / I/O) and `AttributeError` (half-torn session / capture) with
dedicated automated units so regressions in `_DUMP_BEST_EFFORT_ERRORS` are
caught per type, not only via the existing `RuntimeError` smoke.

This debt comes from [PYPOST-876](https://pypost.atlassian.net/browse/PYPOST-876)
tech debt (“Dedicated best-effort units for OSError / AttributeError”).

## Programming Language

Python (pytest agent e2e harness). Guides: `.cursor/lsr/do-python.md`,
`.cursor/lsr/do-testing.md`. Developer docs in English Markdown
(`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **harness maintainer**, I want a unit that forces `OSError` on dump
  I/O so removal from the catch tuple fails CI immediately.
- As a **harness maintainer**, I want a unit that forces `AttributeError`
  on capture so half-torn session misses stay best-effort with WARNING.
- As a **future maintainer**, I want docs to list which best-effort types
  have dedicated unit proof (not only implicit tuple membership).

## Definition of Done

- Dedicated tests prove `OSError` and `AttributeError` are swallowed, log
  `agent_e2e_failure_artifacts_failed`, and return `None` from the dump helper.
- Existing RuntimeError / LookupError propagation tests remain green.
- No lifecycle hook changes (PYPOST-961 owns hook per-type units).
- Unticketed follow-ups (if any) live only in `60-tech-debt.md` (no Jira in
  this run).

## Task Description

**Problem:** PYPOST-876 narrowed the dump helper catch tuple and added
RuntimeError best-effort plus LookupError propagation tests. `OSError` and
`AttributeError` are in the tuple but lack dedicated mocked units — coverage
is implicit.

**Business need:** Per-type locks so tuple edits do not silently drop I/O or
half-torn capture handling.

### In Scope

- Add mocked units in `tests/test_agent_e2e_failure_artifacts.py` for
  `OSError` (write path) and `AttributeError` (`ui_snapshot` capture path).
- Caplog asserts for WARNING + exc type name.
- Update `doc/dev/agent_e2e_failure_artifacts.md` Tests section.

### Out of Scope

- Lifecycle dump-hook per-type units ([PYPOST-961](https://pypost.atlassian.net/browse/PYPOST-961)).
- Shared exception tuple module ([PYPOST-960](https://pypost.atlassian.net/browse/PYPOST-960)).
- Production changes to `pypost/fixtures/agent_e2e_failure.py` (tuple already
  correct from PYPOST-876).
- Creating Jira Debt tickets (orchestrator skip per user directive).
- Commit or Jira status transitions (orchestrator Phase F).

## Functional Requirements

- FR1: Forced `OSError` on dump write → WARNING, `None`, no propagation.
- FR2: Forced `AttributeError` on `ui_snapshot` → WARNING, `None`, no
  propagation.
- FR3: Existing best-effort and propagation tests stay green.
- FR4: Developer docs mention the new dedicated units.

## Non-Functional Requirements

- NFR1: Mocked I/O; no live disk failure required.
- NFR2: Module `pytestmark` timeout retained; no new agent_e2e subprocess tests.
- NFR3: English docs; line length ≤ 100 where practical.

## Constraints and Assumptions

- Parent: PYPOST-876 `_DUMP_BEST_EFFORT_ERRORS` already includes both types.
- Focus on dump helper only; lifecycle hook is PYPOST-961.
- Sprint-task-runner batch: autonomous; no user approval gates.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Dump helper | Writes masked snapshot + diagnostics on test failure |
| Best-effort failure | Expected I/O or capture problem; must not mask assert |
| Harness maintainer | Owns tuple contract and tests |

## Q&A

| Q | A |
| --- | --- |
| Why test-only? | Tuple landed in PYPOST-876; this debt adds per-type locks. |
| Step 3 red if prod OK? | Red gap = missing tests; full asserts added Step 4. |
| Hook OSError units? | Out of scope — PYPOST-961. |
| Jira / commit here? | No — parent orchestrator owns Phase D/F. |
