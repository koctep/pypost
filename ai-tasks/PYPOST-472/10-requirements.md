# PYPOST-472: Deduplicate validation error messages

## Goals

Error strings for environment variable name validation exist in both
`validate_variable_name` (core) and hardcoded `QMessageBox` callers in
`EnvPresenter`. Consolidate to one source of truth so message updates cannot
diverge between validation logic and UI.

## Programming Language

Python 3.10+

## User Stories

- As a user creating a new variable, I want the same error messages as today when
  my name is invalid.
- As a maintainer, I want validation error text defined once so UI and core stay
  in sync.

## Definition of Done

- No hardcoded validation error strings in `EnvPresenter.handle_variable_set_request`.
- All validation failures (including empty after strip) surface messages from
  `validate_variable_name` via `_is_valid_variable_name`.
- Existing tests for validation messaging continue to pass.
- Developer docs reflect single source of truth for user-facing messages.

## Task Description

Technical debt follow-up from PYPOST-163 (item 163-3). PYPOST-478 centralized
rule logic in `pypost/core/variable_name_validation.py`; this task removes the
remaining duplicate empty-name string in the presenter QMessageBox path.

### In Scope

- `EnvPresenter.handle_variable_set_request` — remove inline empty check message.
- Documentation update for UI message sourcing.

### Out of Scope

- Changing validation rules or error wording.
- env_dialog table sync (already uses core validator; no duplicate QMessageBox).
- Dialog title standardization beyond using one validation path.

## Functional Requirements

- After `text.strip()`, presenter must call `_is_valid_variable_name` for all
  invalid cases including empty.
- QMessageBox body text must come from the validator return value only.

## Non-Functional Requirements

- No change to metrics/logging (still in `_is_valid_variable_name`).
- No new dependencies.
