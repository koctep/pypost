# PYPOST-445: Restart-level persistence test for request_timeout

## Context

- **Jira:** PYPOST-445
- **Origin:** Gap from [PYPOST-424](https://pypost.atlassian.net/browse/PYPOST-424) review:
  automated tests cover ConfigManager save/load contracts and SettingsDialog spinbox
  behavior, but no integration test verifies `request_timeout` survives a simulated
  application restart after saving through the settings UI path.
- **Type:** Debt (Sprint follow-up)

## Problem statement

`request_timeout` is exposed in Settings and persisted via `ConfigManager`. Existing tests
assert direct ConfigManager round-trips and dialog accept output, but do not exercise the
full user journey: change timeout in Settings → save to disk → reload after restart →
settings UI reflects the stored value.

## Goals

- Add an integration or end-to-end test that simulates app restart after saving
  `request_timeout` through `SettingsDialog`.
- Assert the value survives on disk and is visible when settings are reopened.

## Scope

### In scope

- One focused test in `tests/test_settings_persistence.py`.
- Developer documentation update referencing the new coverage.

### Out of scope

- Production code changes (unless test reveals a defect).
- Full MainWindow bootstrap or HTTP timeout runtime verification.
- Parametrized matrix of every settings field.

## User stories

- As a **maintainer**, I want a restart-level test so regressions in request timeout
  persistence are caught in CI without manual QA.
- As a **developer**, I want the test to follow existing offscreen Qt and ConfigManager
  isolation patterns.

## Functional requirements

1. **FR-1:** Test drives `SettingsDialog` to change `request_timeout` and accept.
2. **FR-2:** Test saves via `ConfigManager.save_config()` (same path as `MainWindow`).
3. **FR-3:** Test simulates restart with a fresh `ConfigManager().load_config()`.
4. **FR-4:** Test asserts on-disk JSON and reopened dialog spinbox match the saved value.

## Acceptance criteria

1. **AC-1:** New test passes in CI offscreen environment.
2. **AC-2:** Existing settings persistence and dialog tests continue to pass.
3. **AC-3:** No production code changes required unless test reveals a defect.

## Risks and assumptions

| Type | Description |
| ---- | ----------- |
| **Assumption** | ConfigManager + SettingsDialog path is the canonical persistence route for request_timeout. |
| **Assumption** | Fresh `ConfigManager()` after save adequately simulates application restart. |
| **Risk** | Low — test-only change. |

## Programming language

**Python** — PySide6 offscreen pytest in `tests/test_settings_persistence.py`.
