# PYPOST-752: Lint rule for print() in pypost/

## Goals

Close PYPOST-688 finding R-P3-004 by adding a merge gate that prevents new `print()` calls in
application code under `pypost/`. Application errors and diagnostics must use stdlib logging
(PYPOST-742, PYPOST-747).

## User Stories

- As a maintainer, I want CI and `make lint` to fail when someone adds `print()` to `pypost/`,
  so stdout bypass of logging cannot re-enter the codebase unnoticed.

## Definition of Done

| ID | Criterion |
| --- | --- |
| AC-1 | `flake8-print` installed via `make venv-test` and CI test tooling |
| AC-2 | `.flake8` enables T201 for lint runs on `pypost/` |
| AC-3 | Zero current T201 violations in `pypost/` |
| AC-4 | `make check` passes |

## Out of scope

- Linting `scripts/` or `tests/` for print (lint target remains `pypost/` only)
- Replacing existing print in scripts (none in `pypost/` after PYPOST-742)
