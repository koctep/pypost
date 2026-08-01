# PYPOST-962: Dedicated TypeError / ValueError dump best-effort units

## Goals

Lock the agent e2e failure dump helper's best-effort contract for `TypeError`
(malformed capture / snapshot shape) and `ValueError` (invalid capture payload)
with dedicated automated units so regressions in `DUMP_BEST_EFFORT_ERRORS` are
caught per type, not only via implicit tuple membership.

This debt comes from [PYPOST-915](https://pypost.atlassian.net/browse/PYPOST-915)
tech debt (follow-up for remaining tuple members after OSError / AttributeError).

## Programming Language

Python (pytest agent e2e harness). Guides: `.cursor/lsr/do-python.md`,
`.cursor/lsr/do-testing.md`. Developer docs in English Markdown
(`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **harness maintainer**, I want a unit that forces `TypeError` on dump
  capture so removal from the catch tuple fails CI immediately.
- As a **harness maintainer**, I want a unit that forces `ValueError` on dump
  capture so invalid-payload handling stays best-effort with WARNING.
- As a **future maintainer**, I want docs to list which best-effort types have
  dedicated dump-helper unit proof.

## Definition of Done

- Dedicated tests prove `TypeError` and `ValueError` are swallowed, log
  `agent_e2e_failure_artifacts_failed`, and return `None` from the dump helper.
- Existing RuntimeError / OSError / AttributeError / LookupError tests remain
  green.
- No lifecycle hook changes (PYPOST-961 owns hook per-type units).
- No production changes unless tests reveal a contract gap.

## Task Description

**Problem:** PYPOST-915 added dedicated dump-helper units for `OSError` and
`AttributeError`. `TypeError` and `ValueError` remain in
`DUMP_BEST_EFFORT_ERRORS` but lack dedicated mocked units — coverage is
implicit via tuple membership and the RuntimeError smoke test.

**Business need:** Per-type locks so tuple edits do not silently drop malformed
capture or invalid payload handling.

### In Scope

- Add mocked units in `tests/test_agent_e2e_failure_artifacts.py` for
  `TypeError` and `ValueError` on the `ui_snapshot` capture path.
- Caplog asserts for WARNING + exc type name.
- Update `doc/dev/agent_e2e_failure_artifacts.md` Tests section.

### Out of Scope

- Lifecycle dump-hook per-type units ([PYPOST-961](https://pypost.atlassian.net/browse/PYPOST-961)).
- Shared exception tuple module ([PYPOST-960](https://pypost.atlassian.net/browse/PYPOST-960)).
- Production changes to `pypost/fixtures/agent_e2e_failure.py` (tuple already
  correct from PYPOST-876 / PYPOST-960).
- Git commit or Jira Done transition (orchestrator directive).

## Functional Requirements

- FR1: Forced `TypeError` on `ui_snapshot` → WARNING, `None`, no propagation.
- FR2: Forced `ValueError` on `ui_snapshot` → WARNING, `None`, no propagation.
- FR3: Existing best-effort and propagation tests stay green.
- FR4: Developer docs mention the new dedicated units.

## Non-Functional Requirements

- NFR1: Mocked capture; no live disk failure or Qt session required.
- NFR2: Module `pytestmark` timeout retained; no new subprocess tests.
- NFR3: English docs; line length ≤ 100 where practical.

## Constraints and Assumptions

- Parent: [PYPOST-915](https://pypost.atlassian.net/browse/PYPOST-915) established
  dump-helper caplog unit pattern.
- Shared tuple: `DUMP_BEST_EFFORT_ERRORS` in `pypost/agent/e2e_dump_errors.py`
  (PYPOST-960).
- Focus on dump helper only; lifecycle hook is PYPOST-961.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Dump helper | Writes masked snapshot + diagnostics on test failure |
| Best-effort failure | Expected capture problem; must not mask assert |
| Harness maintainer | Owns tuple contract and tests |

## Q&A

| Q | A |
| --- | --- |
| Why test-only? | Tuple landed in PYPOST-876; PYPOST-915 added OSError/AttributeError locks. |
| Step 3 red if prod OK? | Red gap = missing tests; full asserts added Step 4. |
| Hook units? | Out of scope — PYPOST-961. |
| Commit / Jira Done? | No — orchestrator directive. |
