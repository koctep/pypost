# PYPOST-815: Type-check pypost/ui incrementally (R-P2-005c)

## Summary

Follow-up from [PYPOST-734](https://pypost.atlassian.net/browse/PYPOST-734) baseline triage
(R-P2-005c). Extend the mypy baseline gate from `pypost/core/` and `pypost/models/` to
`pypost/ui/` (~64 modules) so Qt presenters and widgets are type-checked incrementally without
fixing all errors upfront.

## Acceptance Criteria

1. `types-PySide6` is a pinned dev dependency (`requirements-dev.in` / `requirements-dev.txt`).
2. `[tool.mypy]` in `pyproject.toml` scopes checks to `pypost/core/`, `pypost/models/`, and
   `pypost/ui/`; `pypost.ui.*` `ignore_errors` override removed.
3. `make typecheck` runs mypy on all three paths and passes when the error set matches the
   committed baseline.
4. UI baseline triage documents 177 known errors across 29 files (categories by error code).
5. All `pypost/ui/` modules include `from __future__ import annotations` (PYPOST-738 pattern).
6. `make check` continues to run lint + tests only (typecheck remains optional).
7. Developer docs describe expanded scope, PySide6 stubs, and UI triage priorities.
8. `make check` and `make typecheck` pass.

## Out of Scope

- Fixing all 177 UI baseline mypy errors in this task.
- Adding mypy to CI or `make check`.
- Type-checking `pypost/fixtures/` (still ignored).

## User Stories

- As a **maintainer**, I want `make typecheck` to cover UI modules so Qt code gets the same
  regression gate as core logic.
- As a **reviewer**, I want UI errors frozen in the baseline so new type regressions fail
  `make typecheck` while known debt is tracked explicitly.
