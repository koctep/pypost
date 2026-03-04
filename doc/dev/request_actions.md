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

High-level flow:
1. User clicks `Actions -> Save` or presses `Ctrl+S`.
2. `RequestWidget.on_save(source=...)` updates request data and emits `save_requested`.
3. `MainWindow.handle_save_request` runs the persistence flow.

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

## Configuration

No new task-specific configuration keys were added.

Observability endpoint configuration remains global and unchanged:
- `settings.metrics_host`
- `settings.metrics_port`

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
