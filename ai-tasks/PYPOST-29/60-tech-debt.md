# PYPOST-29: Technical Debt Analysis

## Shortcuts Taken

- The `+` button position is calculated manually in `MainWindow._position_add_tab_button()` using
  pixel offsets (`+6`) and fixed button size (`24x24`) instead of a layout-managed tab action
  area.
- New-tab trigger source is passed as a free-form string to metrics/logging; current callers are
  controlled, but there is no strict enum/validation at the API boundary.

## Code Quality Issues

- `pypost/ui/main_window.py` continues to accumulate UI orchestration logic in one class, including
  tab action UI placement, metrics calls, and request workflows.
- Hardcoded spacing constants for button placement reduce adaptability for style/font changes and
  high-DPI differences.

## Missing Tests

- No automated UI test verifies that clicking `+` produces the same behavior as `Ctrl+N`.
- No regression test covers `+` button placement after tab add/close/resize operations.
- No test validates `gui_new_tab_actions_total{source=...}` increments for both `plus_button` and
  `shortcut`.

## Performance Concerns

- `_position_add_tab_button()` runs on tab layout changes and resize events. This is low cost for
  current usage, but should be profiled if tab counts become very large or if extra relayout work
  is added later.

## Follow-up Tasks

- Add Qt UI tests for:
  - `+` click path creating one tab.
  - `Ctrl+N` and `+` parity.
  - Button positioning after resize and tab lifecycle operations.
- Refactor tab action controls into a dedicated tab-header component to reduce `MainWindow`
  responsibilities.
- Replace magic spacing constants with named constants and document expected geometry behavior.
- Add a narrow source validation layer for new-tab metrics (`plus_button`, `shortcut`, `unknown`).
