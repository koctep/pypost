# PYPOST-29: Technical Debt Analysis


## Shortcuts Taken

- **Manual `+` button geometry** ([PYPOST-253](https://pypost.atlassian.net/browse/PYPOST-253)):
  `MainWindow._position_add_tab_button()` uses pixel offsets (`+6`) and fixed size (`24x24`)
  instead of a layout-managed tab action area.
- **Untyped new-tab source field** ([PYPOST-254](https://pypost.atlassian.net/browse/PYPOST-254)):
  Metrics/logging take a string source; callers are controlled but there is no enum or validation
  at the API boundary.

## Code Quality Issues

- **MainWindow still a god object** ([PYPOST-255](https://pypost.atlassian.net/browse/PYPOST-255)):
  `main_window.py` keeps accumulating UI logic in one class, including tab placement, metrics, and
  request workflows.
- **Hardcoded tab-button spacing** ([PYPOST-256](https://pypost.atlassian.net/browse/PYPOST-256)):
  Magic spacing constants limit adaptability for fonts, styles, and high-DPI layouts.

## Missing Tests

- No automated UI test verifies that clicking `+` produces the same behavior as `Ctrl+N`.
  — [PYPOST-257](https://pypost.atlassian.net/browse/PYPOST-257)
- No regression test covers `+` button placement after tab add/close/resize operations.
  — [PYPOST-258](https://pypost.atlassian.net/browse/PYPOST-258)
- **New-tab metrics coverage** ([PYPOST-259](https://pypost.atlassian.net/browse/PYPOST-259)):
  No test asserts `gui_new_tab_actions_total{source=...}` for both `plus_button` and `shortcut`.

## Performance Concerns

- **Tab button reposition cost** ([PYPOST-260](https://pypost.atlassian.net/browse/PYPOST-260)):
  `_position_add_tab_button()` runs on tab layout changes and resize; cheap today but worth
  profiling if tab counts or relayout work grow.

## Follow-up Tasks

- **Qt UI tests for new tab** ([PYPOST-261](https://pypost.atlassian.net/browse/PYPOST-261)):
  - `+` click path creating one tab.
  - `Ctrl+N` and `+` parity.
  - Button positioning after resize and tab lifecycle operations.
- **Tab-header component** ([PYPOST-262](https://pypost.atlassian.net/browse/PYPOST-262)):
  Refactor tab controls out of `MainWindow` into a dedicated tab-header component.
- Replace magic spacing constants with named constants and document expected geometry behavior.
  — [PYPOST-263](https://pypost.atlassian.net/browse/PYPOST-263)
- Add a narrow source validation layer for new-tab metrics (`plus_button`, `shortcut`, `unknown`).
  — [PYPOST-264](https://pypost.atlassian.net/browse/PYPOST-264)
