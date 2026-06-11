# PYPOST-293: Layout-Managed Tab Add Button

## Goals

The new-tab `+` control should stay visually aligned with the tab strip without relying on
manual pixel positioning. Layout-managed placement improves maintainability across fonts,
DPI scaling, and future tab-bar styling changes.

## User Stories

- As a user, I want the `+` button to appear immediately after my open tabs so I can open a
  new request tab quickly.
- As a user, I want the `+` button to remain visible and correctly aligned when I add, close,
  or resize tabs.
- As a developer, I want tab add-button placement to use Qt layout/tab-bar APIs instead of
  ad-hoc `move()` calculations so UI changes are easier to maintain.

## Definition of Done

- The `+` button is positioned by Qt tab-bar layout (not manual `move()` on a floating widget).
- Clicking `+` still creates a new request tab via `handle_new_tab("plus_button")`.
- `Ctrl+N` behavior is unchanged.
- Tab cycling shortcuts skip the `+` placeholder tab.
- Closing the `+` placeholder tab has no effect.
- Existing tab presenter tests pass; new tests cover plus-tab behavior.
- Developer docs describe the new approach.

## Task Description

PYPOST-32 introduced a floating `+` button positioned by `TabsPresenter._position_add_tab_button()`
using fixed size (`24x24`) and magic spacing (`6px`). That method ran on every tab layout change
and resize. This follow-up replaces manual geometry with a layout-feasible Qt pattern while
preserving the “after last tab” UX.

## Q&A

- **Q:** Must the button stay directly after the last tab (not in the far corner)?  
  **A:** Yes — same UX as the manual implementation.
- **Q:** Can we use `QTabWidget.setCornerWidget`?  
  **A:** No — corner widget pins to the tab widget edge, not after the last tab when tabs do not
  expand.
- **Q:** Programming language?  
  **A:** Python (PySide6).
