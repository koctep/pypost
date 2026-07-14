# PYPOST-734: Requirements

**Parent:** [PYPOST-687](https://pypost.atlassian.net/browse/PYPOST-687) R-P2-005

## Summary

Add optional static type checking for `pypost/core/` and `pypost/models/` using mypy, exposed
via `make typecheck`, with a frozen error baseline so developers can fix types incrementally
without blocking the main quality gate.

## Acceptance Criteria

1. mypy is a pinned dev dependency (`requirements-dev.in` / `requirements-dev.txt`).
2. `[tool.mypy]` in `pyproject.toml` scopes checks to `pypost/core/` and `pypost/models/`.
3. `make typecheck` runs mypy and passes when the error set matches the committed baseline.
4. Baseline triage documents 54 known errors across 16 files (categories by error code).
5. `make check` continues to run lint + tests only (typecheck remains optional).
6. Developer docs describe usage, baseline updates, and triage priorities.
7. `make check` passes.

## Out of Scope

- Fixing all 54 baseline mypy errors in this task.
- Adding mypy to CI or `make check`.
- Type-checking `pypost/ui/` (Qt-heavy; deferred).

## User Stories

- As a **maintainer**, I want `make typecheck` so I can run static analysis on core logic
  without installing tools ad hoc.
- As a **reviewer**, I want a baseline gate so new type errors fail `make typecheck` while
  known debt is tracked explicitly.
