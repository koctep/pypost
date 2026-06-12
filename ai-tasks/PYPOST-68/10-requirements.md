# PYPOST-68: Hide EnvPresenter internal widgets

## Programming language

Python — per `.cursor/lsr/do-python.md`.

## Goals

Resolve PYPOST-43 TD-3: `EnvPresenter` must not expose internal `QLabel` / `QComboBox` /
`QPushButton` instances via public properties. Callers use intent methods instead.

## Problem statement

`EnvPresenter` exposed `env_selector`, `manage_btn`, `mcp_status_label`, `env_label`,
`mcp_tools_btn`, and `mcp_activity_btn` so `MainWindow.apply_settings` could call `setFont`
on each widget. PYPOST-106 moved font propagation to global QSS; the properties remain as
leaky encapsulation.

## Functional requirements

- **FR-1:** Remove widget-exposure properties from `EnvPresenter`.
- **FR-2:** Add `apply_font(font: QFont)` that sets font on all env-bar widgets.
- **FR-3:** `apply_settings` delegates font to `apply_font` via `QApplication.font()`.
- **FR-4:** Add public query/intent methods for environment selection and MCP bar labels
  used by tests (`select_environment_index`, `environment_at`, etc.).
- **FR-5:** Keep `widget` property for layout integration.

## Non-functional requirements

- **NFR-1:** Minimal diff; no behavior change for users.
- **NFR-2:** Existing tests updated; add coverage for `apply_font`.

## Out of scope

- Refactoring other presenters' font APIs (PYPOST-43 TD-1).
- Changing env-selection or MCP lifecycle behavior.

## Definition of Done

| # | Criterion |
|---|-----------|
| AC-1 | No public widget-exposure properties on `EnvPresenter` |
| AC-2 | `apply_font` sets font on all env-bar widgets |
| AC-3 | `apply_settings` calls `apply_font` |
| AC-4 | Tests use public API; all pass |
