# PYPOST-900: Optional public fixture-drive helper

## Goals

Packaging unit tests that drive pytest yield fixtures outside a request currently
call the private pytest API `FixtureFunctionDefinition._get_wrapped_function()`.
Maintainers need a small shared helper under `tests/helpers/` so future packaging
(or similar) tests isolate pytest API churn in one place.

## Programming Language

Python 3.10+

## User Stories

- As a **maintainer**, I want packaging log tests to use a shared fixture-drive
  helper instead of inline private pytest unwrap calls, so pytest internals
  changes require updates in one module only.
- As a **contributor**, I want the helper documented in developer testing docs,
  so I can reuse it when adding similar caplog proofs.
- As a **desktop user** (indirect), I want this debt work not to change product
  behavior — only test harness ergonomics.

## Definition of Done

- A helper module under `tests/helpers/` exposes unwrap and drive utilities for
  yield fixtures (private `_get_wrapped_function` isolated there).
- `tests/test_agent_e2e_packaging_logs.py` uses the helper (no direct private
  pytest calls in that module).
- Helper has focused unit coverage with explicit timeout marker.
- Steps 1–8 task artifacts exist for PYPOST-900.
- No production code changes.

## Task Description

**Problem:** PYPOST-867 packaging caplog proofs inline
`fixture._get_wrapped_function()` and local generator drive logic. Step 7 noted
optional polish: centralize in `tests/helpers/` for pytest API isolation. Source:
[PYPOST-900](https://pypost.atlassian.net/browse/PYPOST-900), from
[PYPOST-867](https://pypost.atlassian.net/browse/PYPOST-867)
`ai-tasks/PYPOST-867/60-tech-debt.md` — Optional public fixture-drive helper.

**Business need:** Lowest-priority test harness debt — reduce duplication and
pytest coupling before more packaging unit tests adopt the same pattern.

### In Scope

- New `tests/helpers/` fixture-drive helper.
- Refactor existing packaging log tests to consume it.
- Unit test for the helper API.
- Developer doc cross-link in testing docs.

### Out of Scope

- Changing packaging fixture behavior or production logging.
- Replacing live-session caplog smokes (PYPOST-899).
- Broader pytest plugin refactors.

## Functional Requirements

- FR1: Helper module lives under `tests/helpers/` and wraps private pytest
  unwrap (`_get_wrapped_function`).
- FR2: Helper provides drive-through for yield-fixture generators (setup +
  teardown via `StopIteration`).
- FR3: `tests/test_agent_e2e_packaging_logs.py` imports and uses the helper;
  no `_get_wrapped_function` calls remain in that file.
- FR4: Helper module is covered by at least one automated test with explicit
  timeout marker.

## Non-Functional Requirements

- NFR1: Explicit per-module or per-test `pytest.mark.timeout` on new tests.
- NFR2: Minimal API surface — only what packaging log tests need today.
- NFR3: flake8-clean, line length ≤ 100.

## Q&A

| Question | Answer |
| --- | --- |
| Source of the debt item? | [PYPOST-867 tech debt](../PYPOST-867/60-tech-debt.md) → PYPOST-900. |
| Production changes? | No — test-only refactor. |
| Name of helper module? | `tests/helpers/fixture_drive.py` (fixture-drive helper). |
