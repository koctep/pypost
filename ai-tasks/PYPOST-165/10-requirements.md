# PYPOST-165: Add validation for variable names in environment UI

## Goals

Users editing environment variables in Manage Environments must not persist names that break
Jinja2 template rendering. Invalid names should be rejected with clear feedback, matching the
behaviour already available when creating variables from the response view.

## Programming Language

Python 3.10+

## User Stories

- As a user, when I type an invalid variable name in Manage Environments, I see why it was
  rejected and the table reverts to the previous valid key.
- As a maintainer, I want one shared validation rule set for all environment variable naming
  flows so behaviour stays consistent.

## Definition of Done

- Manage Environments variable key edits use shared Jinja2-compatible validation rules.
- Invalid names are not saved to the environment model.
- The user sees the same error messages as the response-view new-variable flow.
- Automated tests cover reject-and-revert behaviour and error dialog invocation.
- Developer docs describe validation in the environments dialog.

## Task Description

Source: `ai-tasks/PYPOST-22/40-tech-debt.md` — "Add validation for variable names."

### In Scope

- Manage Environments variables table (`EnvironmentVariablesWidget`).
- Reuse `validate_environment_variable_name` / `validate_variable_name` from core.
- User-facing error dialog via existing `show_invalid_variable_name_error`.

### Out of Scope

- Changing validation rules or adding new rules.
- Metrics/logging parity with `EnvPresenter` (pre-existing gap; see tech-debt notes).
- Validating or renaming variables already stored on disk.

## Q&A

- **Q:** Duplicate work with PYPOST-471? **A:** PYPOST-471 wired silent revert; this task
  completes the follow-up from PYPOST-22 with user-visible feedback and test/doc closure.
