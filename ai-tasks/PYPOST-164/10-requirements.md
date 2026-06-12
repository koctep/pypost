# PYPOST-164: Qt tests for ResponseView context menu

## Goals

PYPOST-22 added a custom response-body context menu (Set Variable, Copy, Select All) but
deferred automated GUI coverage. Without tests, menu composition and signal dispatch can
regress silently when `ResponseView` is refactored.

## Programming Language

Python 3.10+

## User Stories

- As a maintainer, I want automated Qt tests for the response context menu so menu items and
  signal emission stay correct after UI changes.
- As a maintainer, I want coverage for env-key submenu wiring so Set Variable and New
  Variable flows remain trustworthy.
- As a contributor, I want dev docs to list the new test module alongside existing GUI patterns.

## Definition of Done

- Automated Qt-level tests exercise `ResponseView.show_context_menu` with mocked `QMenu`.
- Without env keys, Set Variable submenu is omitted; Copy and Select All remain available
  when text is selected.
- With env keys and non-empty selection, Set Variable submenu lists keys and New Variable.
- Selecting an env key emits `variable_set_requested(key, value)`; New Variable emits
  `(None, value)`.
- Copy and Select All actions wire to `body_view.copy` and `body_view.selectAll`.
- Whitespace-only selection skips Set Variable submenu.
- All new and existing related tests pass.
- Developer docs reference the new test module.

## Task Description

Source: `ai-tasks/PYPOST-22/40-tech-debt.md` — "No UI tests for context menu interaction."

### In Scope

- `ResponseView.show_context_menu` menu composition and action dispatch.
- Qt tests consistent with `test_history_panel.py` and `test_response_view_search.py`.

### Out of Scope

- Full MainWindow / EnvPresenter integration (covered by `test_new_variable_flow_integration.py`).
- Collection tree, tab bar, or env-dialog context menus (already covered elsewhere).
- New observability metrics or logging.

## Q&A

- **Q:** Unit tests on `ResponseView` or full MainWindow? **A:** Widget-level Qt tests with
  mocked `QMenu`, matching existing PyPost GUI test conventions (PYPOST-365).
- **Q:** Tabs or env context menus? **A:** Response body menu from PYPOST-22; env list and
  vars table menus already have coverage in `test_env_dialog.py`.
