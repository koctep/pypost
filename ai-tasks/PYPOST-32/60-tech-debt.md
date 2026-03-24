# PYPOST-32: Technical Debt Analysis


## Shortcuts Taken

- **Manual `+` button geometry** ([PYPOST-293](https://pypost.atlassian.net/browse/PYPOST-293)):
  `MainWindow._position_add_tab_button()` uses pixel offsets (`+6`) and fixed size (`24x24`)
  instead of a layout-managed tab action area.
- **Untyped new-tab source field** ([PYPOST-294](https://pypost.atlassian.net/browse/PYPOST-294)):
  Metrics/logging take a string source; callers are controlled but there is no enum or validation
  at the API boundary.

## Code Quality Issues

- **MainWindow still a god object** ([PYPOST-295](https://pypost.atlassian.net/browse/PYPOST-295)):
  `main_window.py` keeps accumulating UI logic in one class, including tab placement, metrics, and
  request workflows.
- **Hardcoded tab-button spacing** ([PYPOST-296](https://pypost.atlassian.net/browse/PYPOST-296)):
  Magic spacing constants limit adaptability for fonts, styles, and high-DPI layouts.

## Missing Tests

- No automated UI test verifies `+` click matches `Ctrl+N` new-tab behavior.
  — [PYPOST-297](https://pypost.atlassian.net/browse/PYPOST-297)
- No regression test covers `+` button placement after tab add/close/resize.
  — [PYPOST-298](https://pypost.atlassian.net/browse/PYPOST-298)
- **New-tab metrics coverage** ([PYPOST-299](https://pypost.atlassian.net/browse/PYPOST-299)):
  No test asserts `gui_new_tab_actions_total{source=...}` for both `plus_button` and `shortcut`.

## Performance Concerns

- **Tab button reposition cost** ([PYPOST-300](https://pypost.atlassian.net/browse/PYPOST-300)):
  `_position_add_tab_button()` runs on tab layout changes and resize; cheap today but worth
  profiling if tab counts or relayout work grow.

## Follow-up Tasks

- **Qt UI tests for new tab** ([PYPOST-301](https://pypost.atlassian.net/browse/PYPOST-301)):
  - `+` click path creating one tab.
  - `Ctrl+N` and `+` parity.
  - Button positioning after resize and tab lifecycle operations.
- **Tab-header component** ([PYPOST-302](https://pypost.atlassian.net/browse/PYPOST-302)):
  Refactor tab controls out of `MainWindow` into a dedicated tab-header component.
- Replace magic spacing constants with named constants and document expected geometry behavior.
  — [PYPOST-303](https://pypost.atlassian.net/browse/PYPOST-303)
- Add a narrow source validation layer for new-tab metrics (`plus_button`, `shortcut`, `unknown`).
  — [PYPOST-304](https://pypost.atlassian.net/browse/PYPOST-304)
