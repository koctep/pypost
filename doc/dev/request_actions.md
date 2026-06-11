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
- **`RequestTabHeader` (`pypost/ui/widgets/tab_header.py`)**:
  - Owns request tab-bar chrome: closable tab setup, trailing plus placeholder tab, and label
    text updates via `set_tab_label`.
  - Emits `new_tab_requested` when the user clicks the `+` tab; wired to
    `TabsPresenter.handle_new_tab("plus_button")`.
- **`TabsPresenter` (`pypost/ui/presenters/tabs_presenter.py`)**:
  - Receives `save_requested` and `save_as_requested` from each `RequestWidget`.
  - Delegates persistence to `RequestSaveOrchestrator` and updates tab state/signals.
  - Composes `RequestTabHeader` for tab-bar controls; routes `Ctrl+N` to
    `handle_new_tab(source=...)`.
- **`RequestSaveOrchestrator` (`pypost/ui/request_save_orchestrator.py`)**:
  - Owns save/save-as dialogs, overwrite/stale confirmations, and `RequestManager` calls.
  - Returns `SaveResult` for the presenter to apply tab updates.
- **`MainWindow` (`pypost/ui/main_window.py`)**:
  - Wires `request_saved` / `request_save_as_completed` to collections tree refresh.
  - Delegates tab widget and new-tab shortcuts to `TabsPresenter`.
- **`MetricsManager` (`pypost/core/metrics.py`)**:
  - Collects GUI action metrics:
    - `gui_send_clicks_total`
    - `gui_save_actions_total{source=<menu|shortcut>}`
    - `gui_new_tab_actions_total{source=<plus_button|shortcut|unknown>}`

High-level flow:
1. User clicks `Actions -> Save` or presses `Ctrl+S`.
2. `RequestWidget.on_save(source=...)` updates request data and emits `save_requested`.
3. `TabsPresenter` calls `RequestSaveOrchestrator.save_request` and emits `request_saved`.

New-tab flow:
1. User clicks `+` (plus tab) or presses `Ctrl+N`.
1. `TabsPresenter.handle_new_tab(source=...)` logs source and request-tab count before action.
1. `MetricsManager.track_gui_new_tab_action(source)` increments labeled metric.
1. `TabsPresenter.add_new_tab()` inserts and selects a new request tab before the plus placeholder.

Save-as flow:
1. User clicks `Actions -> Save As...` or presses `Ctrl+Shift+S`.
1. `RequestWidget.on_save_as(source=...)` updates request data and emits
   `save_as_requested`.
1. `RequestSaveOrchestrator.save_as_request` opens save dialog and persists a new request ID.
1. `Save As...` uses a UI snapshot copy of request data; source request is not mutated in-place.

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

### `RequestWidget.on_save_as(source: str = "unknown")`

Triggers save-as from UI action entry points.

- **source**: save-as origin (`menu`, `shortcut`, or fallback value).
- **Behavior**:
  1. Writes INFO log `save_as_action_triggered source=<source>`.
  1. Increments metric `gui_save_as_actions_total{source=<source>}`.
  1. Emits `save_as_requested` with a copied `RequestData` snapshot from UI fields.

### `RequestWidget.get_request_data_from_ui()`

Builds a deep-copied `RequestData` snapshot from current editor widgets.

- Used by `send`, `save`, and `save as` actions.
- Prevents unintended mutation of the original opened entity before explicit save operations.

### `RequestWidget.handle_save_as_menu_action()`

Menu callback for `Actions -> Save As...`. Calls `on_save_as("menu")`.

### `RequestWidget.handle_save_as_shortcut()`

Shortcut callback for `Ctrl+Shift+S`. Calls `on_save_as("shortcut")`.

### `MetricsManager.track_gui_save_action(source: str)`

Records a labeled counter increment for save action source.

### `TabsPresenter.handle_new_tab(source: str = "unknown")`

Centralized new-tab entry point used by both keyboard and plus-tab flows.

- **source**: trigger origin (`plus_button`, `shortcut`, fallback `unknown`).
- **Behavior**:
  1. Writes INFO log `new_tab_action_triggered source=<source> tabs_before=<count>`.
  1. Increments metric `gui_new_tab_actions_total{source=<source>}`.
  1. Calls `add_new_tab()` once (inserts before the plus placeholder tab).

### Plus placeholder tab (`RequestTabHeader.ensure_plus_tab()`)

Layout-managed `+` control using Qt tab-bar APIs:

- Trailing tab marked with `PLUS_TAB_MARKER` in `QTabBar.tabData`.
- `+` widget attached via `QTabBar.setTabButton(..., LeftSide, ...)`.
- `tabBarClicked` on the plus index emits `new_tab_requested` → `handle_new_tab("plus_button")`.
- Close requests on the plus tab are ignored; tab cycling skips the placeholder.
- Use `_request_tab_count()` (or filter `RequestTab` widgets) instead of raw `QTabWidget.count()`.

### `RequestTabHeader.set_tab_label(index, label)`

Updates tab title text after collection renames or save flows. `TabsPresenter` still matches tabs
by request id before calling this helper.

### `MainWindow.handle_new_tab(source: str = "unknown")`

MainWindow delegate — forwards to `TabsPresenter.handle_new_tab()`.

### `MetricsManager.track_gui_new_tab_action(source: str)`

Records a labeled counter increment for new-tab trigger source.

### `MetricsManager.track_gui_save_as_action(source: str)`

Records a labeled counter increment for save-as trigger source.

## Configuration

No new task-specific configuration keys were added.

Observability endpoint configuration remains global and unchanged:
- `settings.metrics_host`
- `settings.metrics_port`

Tab action UI uses internal constants in `RequestTabHeader`:
- Plus button size: `ADD_TAB_BUTTON_SIZE` (24px)
- Plus tab marker: `PLUS_TAB_MARKER` (`pypost_plus_tab`)

## Testing

Save-as orchestrator tests live in `tests/test_request_save_orchestrator.py` (mocked
`SaveRequestDialog`):

| Test | Behavior verified |
| ---- | ----------------- |
| `test_save_as_assigns_new_request_id` | Happy path: new UUID, dialog name, target collection |
| `test_save_as_cancelled_when_dialog_dismissed` | User dismisses dialog → no persistence |
| `test_save_as_cancelled_when_missing_target_collection` | No collection selected/created → cancelled |
| `test_save_as_creates_new_collection_via_dialog` | New collection name from dialog is created and used |
| `test_save_as_expands_target_collection` | Target collection added to expanded state |
| `test_save_as_preserves_source_request_in_manager` | Source entity on disk unchanged; copy persisted separately |

Presenter-level save-as coverage in `tests/test_tabs_presenter.py`:

- `test_save_as_preserves_original_request_id` — tab rebound to new ID; source ID unchanged in
  manager and input snapshot.
- `test_save_as_emits_request_save_as_completed_not_request_saved` — save-as emits
  `request_save_as_completed` (not `request_saved`) with the new ID.

Run:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest \
  tests/test_request_save_orchestrator.py tests/test_tabs_presenter.py -k save_as -v
```

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

### Save-as shortcut does nothing

- Verify `_setup_shortcuts` in `RequestWidget` binds `Ctrl+Shift+S`.
- Confirm focus remains in the request tab widget and shortcut is not intercepted globally.

### Save-as metric is missing

- Ensure `gui_save_as_actions_total` is registered in `MetricsManager._init_metrics()`.
- Trigger `Actions -> Save As...` and `Ctrl+Shift+S`, then inspect `/metrics`.

### Save action works but data is not persisted

- Inspect `RequestSaveOrchestrator.save_request` and `TabsPresenter._handle_save_request`.
- Check collection and storage files for write permissions.

### `+` button is not visible or overlaps tabs

- Confirm `RequestTabHeader.tab_bar.setExpanding(False)` is active after attach.
- Verify the plus placeholder tab exists (`plus_tab_index() >= 0`) and is the last tab.
- Check `QTabBar.setTabButton` still attaches the `+` widget on the plus tab index.

### `Ctrl+N` works but `+` click does nothing

- Confirm `tabBarClicked` on the plus index calls `handle_new_tab("plus_button")`.
- Verify `handle_new_tab` still calls `add_new_tab()` (not an early return path).

### New-tab metrics are missing

- Ensure `gui_new_tab_actions_total` is registered in `MetricsManager._init_metrics()`.
- Trigger at least one `Ctrl+N` and one `+` click before checking `/metrics`.
