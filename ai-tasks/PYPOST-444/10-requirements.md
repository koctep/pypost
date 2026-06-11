# PYPOST-444: Qt-level test for settings save validation path

## Context

- **Jira:** PYPOST-444
- **Origin:** Technical debt from [PYPOST-423](https://pypost.atlassian.net/browse/PYPOST-423)
  review: parser and unit tests cover retryable status codes validation, but no automated
  Qt dialog test asserts blocked save and warning behavior in `SettingsDialog.accept()`.
- **Type:** Debt (Sprint follow-up)

## Problem statement

When a user enters invalid retryable HTTP status codes in Settings and clicks Save,
`SettingsDialog.accept()` must block persistence, show a warning dialog, and log a structured
WARNING. Parser unit tests prove validation logic; helper unit tests prove
`show_invalid_retryable_status_codes` wiring. The dialog-level orchestration in `accept()` is
not covered by an offscreen Qt test.

## Goals

- Add a focused offscreen Qt test that exercises the invalid retryable codes save path through
  `SettingsDialog.accept()`.
- Assert save is blocked (`new_settings` remains unset).
- Assert the warning helper is invoked with the validation message.
- Assert the existing structured WARNING log line is emitted.

## Scope

### In scope

- One or more tests in `tests/test_settings_dialog.py` for invalid retryable codes on save.
- Developer documentation updates referencing the new coverage.

### Out of scope

- Changing validation rules, dialog UI, or logging in production code.
- Full matrix of every parser failure reason (covered by `test_retryable_status_codes_parse.py`).
- `pytest-qt` adoption or new test infrastructure.

## User stories

- As a **maintainer**, I want a Qt-level test so regressions in the settings save validation
  path are caught in CI without manual QA.
- As a **developer**, I want the test to follow existing offscreen Qt patterns (patch dialog
  helpers, `caplog` for WARNING).

## Functional requirements

1. **FR-1:** Test constructs `SettingsDialog` offscreen with invalid retryable codes text.
2. **FR-2:** Calling `accept()` does not set `new_settings`.
3. **FR-3:** `show_invalid_retryable_status_codes` is called with parent dialog and parser
   message.
4. **FR-4:** WARNING log `retryable_codes_settings_validation_failed` with `reason=` is
   recorded (caplog contract).

## Acceptance criteria

1. **AC-1:** New test passes in CI offscreen environment.
2. **AC-2:** Existing `tests/test_settings_dialog.py` tests continue to pass.
3. **AC-3:** No production code changes required unless test reveals a defect.

## Risks and assumptions

| Type | Description |
| ---- | ----------- |
| **Assumption** | Validation behavior from PYPOST-423 is correct and stable. |
| **Assumption** | Patching `show_invalid_retryable_status_codes` at the settings_dialog import site matches project GUI test conventions. |
| **Risk** | Low — test-only change. |

## Programming language

**Python** — PySide6 offscreen pytest in `tests/test_settings_dialog.py`.
