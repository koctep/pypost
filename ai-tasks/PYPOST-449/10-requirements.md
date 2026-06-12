# PYPOST-449: Further decompose EnvironmentDialog variable row update logic

## Goals

Environment variable editing works but the row update flow in the variables table remains
dense and hard to maintain. This follow-up from PYPOST-437 improves readability and
testability by extracting row-level helpers without changing user-visible behavior.

Source: [PYPOST-449](https://pypost.atlassian.net/browse/PYPOST-449) (Jira, type: Debt,
priority: Low).

## Programming Language

Python

## User Stories

- As a developer, I want row update logic split into focused helpers, so I can reason about
  key/value/hidden transitions without reading one large method.
- As a developer, I want unit tests that target the variables widget directly, so regressions
  in row updates are caught without full dialog setup.
- As a user, I want environment variable editing to behave exactly as before, so this refactor
  does not disrupt my workflow.

## Definition of Done

1. Row-level helpers are extracted for invalid-key revert, hidden-value resolution on edit,
   and hidden-toggle value-cell refresh in `EnvironmentVariablesWidget`.
2. `on_var_changed`, `_sync_env_variables_from_table`, and `_on_hidden_toggled` delegate to
   helpers; behavior is unchanged.
3. Existing `tests/test_env_dialog.py` passes without modification.
4. New focused tests cover the extracted row-update paths on `EnvironmentVariablesWidget`.
5. Developer documentation notes the helper decomposition.

## Task Description

### Problem Statement

After PYPOST-437 and PYPOST-496, value-item helpers exist (`_make_value_item`,
`_extract_real_value`) but the row rebuild path (`on_var_changed` →
`_sync_env_variables_from_table`) and hidden-toggle updates remain intertwined.

### Scope

- In scope: helper extraction in `environment_variables_widget.py`; widget-level tests;
  dev-doc update.
- Out of scope: new UI features, logging policy changes, presenter/dialog API changes.

### Constraints and Assumptions

- No behavior change — regression tests are the acceptance gate.
- Helpers remain widget methods (Qt table access required).

## Non-Functional Requirements

- Maintainability: each helper has a single responsibility in the row-update flow.
- Testability: helpers are covered by direct widget tests where practical.
- Compatibility: `EnvironmentDialog` delegation and integration tests unchanged.

## Q&A

- Q: Why is this needed?
  - A: PYPOST-437 tech-debt noted remaining complexity in row-level flow; PYPOST-449 closes
    that follow-up.
- Q: Does this change hidden masking or validation rules?
  - A: No. Only structure changes; rules stay in existing validators and value-item helpers.
