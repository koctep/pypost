# PYPOST-114: Variable tooltip QSS architecture

## Current state

- `VariableHoverMixin._show_or_hide_tooltip` and `VariableAwareTableWidget` call
  `QToolTip.showText(global_pos, text, widget)`.
- `StyleManager.load_styles()` merges `pypost/ui/styles/*.qss` and applies via
  `QApplication.setStyleSheet()`.
- `main.qss` had menu and tree rules but no `QToolTip` selector.

## Decision

Add a global `QToolTip { ... }` block to `main.qss` using `palette(tooltip-text)`,
`palette(tooltip-base)`, and `palette(mid)` so colors follow the active Qt theme without
hardcoded literals in Python.

Variable hover tooltips automatically inherit this rule because `QToolTip.showText` renders
the shared Qt tooltip widget styled by the application stylesheet.

## Implementation plan

1. Append `QToolTip` rules to `main.qss` with a short comment linking to variable hover.
2. Extend `tests/test_style_manager_font.py` with `test_load_styles_includes_tooltip_qss`.
3. Document the hook in `doc/dev/ui_mixins.md` and cross-link from `ui_font_and_styles.md`.

## Risks

| Risk | Mitigation |
| --- | --- |
| Platform ignores some QToolTip QSS on macOS | Document limitation; palette roles still work on Windows/Linux |
| Global rule affects all tooltips | Acceptable — consistent UX; same pattern as QMenu rules |
