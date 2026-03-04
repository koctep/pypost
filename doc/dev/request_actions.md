# Request Actions

## Overview

The request editor on the main screen groups request-level commands near the URL bar.
`Send` is a direct button and `Save` is available via an `Actions` menu button placed to
the right of `Send`.

This design reduces UI clutter and allows adding more actions in the same menu later.

## Architecture

- **`RequestWidget` (`pypost/ui/widgets/request_editor.py`)**:
  - Builds action controls for each request tab.
  - Owns `Send` button, `Actions` tool button, and `Save` menu action.
- **`MainWindow` (`pypost/ui/main_window.py`)**:
  - Receives `save_requested` and `send_requested` signals.
  - Executes the existing save workflow via `handle_save_request`.
- **`MetricsManager` (`pypost/core/metrics.py`)**:
  - Collects GUI action metrics:
    - `gui_send_clicks_total`
    - `gui_save_actions_total{source=<menu|shortcut>}`
    - `gui_new_tab_actions_total{source=<plus_button|shortcut|unknown>}`
- **`MainWindow` tab controls (`pypost/ui/main_window.py`)**:
  - Defines `TabBarWithAddButton` (custom `QTabBar`) to emit layout-change notifications.
  - Places a `+` tab action button (`add_tab_btn`) next to the last tab.
  - Routes both `Ctrl+N` and `+` click to `handle_new_tab(source=...)`.

High-level flow:
1. User clicks `Actions -> Save` or presses `Ctrl+S`.
2. `RequestWidget.on_save(source=...)` updates request data and emits `save_requested`.
3. `MainWindow.handle_save_request` runs the persistence flow.

New-tab flow:
1. User clicks `+` or presses `Ctrl+N`.
1. `MainWindow.handle_new_tab(source=...)` logs source and tab count before action.
1. `MetricsManager.track_gui_new_tab_action(source)` increments labeled metric.
1. `MainWindow.add_new_tab()` creates and selects the new request tab.

## API / Usage

### `RequestWidget.on_save(source: str = "unknown")`

Triggers save from UI action entry points.

- **source**: save origin (`menu`, `shortcut`, or fallback value).
- **Behavior**:
  1. Writes INFO log `save_action_triggered source=<source>`.
  1. Increments metric `gui_save_actions_total{source=<source>}`.
  1. Emits `save_requested` with current `RequestData`.

### `RequestWidget.handle_save_menu_action()`

Menu callback for `Actions -> Save`. Calls `on_save("menu")`.

### `RequestWidget.handle_save_request_shortcut()`

Shortcut callback for `Ctrl+S`. Calls `on_save("shortcut")`.

### `MetricsManager.track_gui_save_action(source: str)`

Records a labeled counter increment for save action source.

### `MainWindow.handle_new_tab(source: str = "unknown")`

Centralized new-tab entry point used by both keyboard and button flows.

- **source**: trigger origin (`plus_button`, `shortcut`, fallback `unknown`).
- **Behavior**:
  1. Writes INFO log `new_tab_action_triggered source=<source> tabs_before=<count>`.
  1. Increments metric `gui_new_tab_actions_total{source=<source>}`.
  1. Calls `add_new_tab()` once.

### `MainWindow._position_add_tab_button()`

Positions `add_tab_btn` relative to `QTabWidget`/`QTabBar` geometry.

- Uses last tab rect when tabs exist.
- Uses left offset baseline when no tabs exist.
- Clamps X position to widget bounds to avoid clipping.
- Triggered on tab layout changes, resize, and tab add/close operations.

### `MetricsManager.track_gui_new_tab_action(source: str)`

Records a labeled counter increment for new-tab trigger source.

## Configuration

No new task-specific configuration keys were added.

Observability endpoint configuration remains global and unchanged:
- `settings.metrics_host`
- `settings.metrics_port`

Tab action UI uses internal constants in `MainWindow`:
- Button size: `24x24`
- Horizontal spacing offset: `6px`

## Troubleshooting

### `Save` is not visible in main screen

- Check that the request tab uses `RequestWidget` from
  `pypost/ui/widgets/request_editor.py`.
- Confirm `actions_btn` and `actions_menu` are created in `init_ui`.

### `Ctrl+S` does not save

- Verify `_setup_shortcuts` binds `Ctrl+S` to `handle_save_request_shortcut`.
- Confirm no global shortcut conflict in the active window manager.

### Save metric does not appear in Prometheus output

- Ensure metrics server is running (`pypost/main.py` starts `MetricsManager`).
- Trigger save at least once and inspect `/metrics` for
  `gui_save_actions_total{source="menu"}` or `source="shortcut"`.

### Save action works but data is not persisted

- Inspect `MainWindow.handle_save_request` flow.
- Check collection and storage files for write permissions.

### `+` button is not visible or overlaps tabs

- Confirm `self.tab_bar.setExpanding(False)` is active.
- Verify `_position_add_tab_button()` is called after tab add/close and on layout changes.
- Check that the position clamp (`max_x`) still uses current tab widget width.

### `Ctrl+N` works but `+` click does nothing

- Confirm `add_tab_btn.clicked` is connected to `handle_new_tab("plus_button")`.
- Verify `handle_new_tab` still calls `add_new_tab()` (not an early return path).

### New-tab metrics are missing

- Ensure `gui_new_tab_actions_total` is registered in `MetricsManager._init_metrics()`.
- Trigger at least one `Ctrl+N` and one `+` click before checking `/metrics`.
