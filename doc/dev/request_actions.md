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
  - Emits `new_tab_requested` when the user clicks the embedded `+` button (primary path via
    `plus_btn.clicked`) or the plus-tab chrome outside the button (fallback via
    `tabBarClicked`); wired to `TabsPresenter.handle_new_tab("plus_button")`.
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
    - `gui_new_tab_actions_total{source=<plus_button|shortcut|collections_context|unknown>}`

High-level flow:
1. User clicks `Actions -> Save` or presses `Ctrl+S`.
2. `RequestWidget.on_save(source=...)` updates request data and emits `save_requested`.
3. `TabsPresenter` calls `RequestSaveOrchestrator.save_request` and emits `request_saved`.

New-tab flow:
1. User clicks the embedded `+` `QPushButton` (primary), clicks plus-tab chrome outside the
   button (fallback), or presses `Ctrl+N`.
1. `RequestTabHeader` emits `new_tab_requested` (`plus_btn.clicked` or `_on_tab_bar_clicked`).
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

- **source**: trigger origin (`plus_button`, `shortcut`, `collections_context`, fallback `unknown`).
- **Behavior**:
  1. Writes INFO log `new_tab_action_triggered source=<source> tabs_before=<count>`.
  1. Increments metric `gui_new_tab_actions_total{source=<source>}`.
  1. Calls `add_new_tab()` once (inserts before the plus placeholder tab).

### Plus placeholder tab (`RequestTabHeader.ensure_plus_tab()`)

Layout-managed `+` control using Qt tab-bar APIs:

- Trailing tab marked with `PLUS_TAB_MARKER` in `QTabBar.tabData`.
- `+` widget attached via `QTabBar.setTabButton(..., LeftSide, ...)`.
- **Primary click path**: `plus_btn.clicked` → `new_tab_requested` →
  `handle_new_tab("plus_button")`. Required because `QTabBar.tabBarClicked` does not fire when
  the user clicks an embedded tab-button widget (Qt routes the event to the child).
- **Fallback click path**: `_on_tab_bar_clicked` on `tabBarClicked` at the plus index emits
  `new_tab_requested` when the user clicks plus-tab chrome outside the embedded button.
- Close requests on the plus tab are ignored; tab cycling skips the placeholder.
- After a request tab is removed, if any request tabs remain and Qt left current on `+`
  (common when closing the rightmost request tab), the presenter reselects via
  `_ensure_current_is_navigable(preferred_index)`, which uses `navigable_tab_indices()`
  (prefer the previous request tab; fall back to the last navigable). Both single close
  (`close_tab`, PYPOST-824) and bulk close (`close_tabs_for_request_ids`, PYPOST-831)
  share that helper. Bulk preferred index is left of the leftmost closed tab.
- Use `_request_tab_count()` (or filter `RequestTab` widgets) instead of raw `QTabWidget.count()`.

### `RequestTabHeader.set_tab_label(index, label)`

Updates tab title text after collection renames or save flows. `TabsPresenter` still matches tabs
by request id before calling this helper.

### `MainWindow.handle_new_tab(source: str = "unknown")`

MainWindow delegate — forwards to `TabsPresenter.handle_new_tab()`.

### `MetricsManager.track_gui_new_tab_action(source: str)`

Records a labeled counter increment for new-tab trigger source. The metrics registry
normalizes `source` via `_normalize_new_tab_source`: allowed labels are `plus_button`,
`shortcut`, `collections_context`, and `unknown`; any other string is recorded as `unknown`.

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

Plus-tab click tests in `tests/test_tab_header.py` and `tests/test_tabs_presenter.py` cover
both click paths:

- **Primary**: `QTest.mouseClick` on the real embedded `+` button (`tabButton(plus_idx, LeftSide)`)
  — matches user clicks on the visible widget wired via `plus_btn.clicked`.
- **Fallback**: `tabBarClicked.emit(plus_idx)` — covers `_on_tab_bar_clicked` when the user
  clicks plus-tab chrome outside the embedded button.

| Test | Behavior verified |
| ---- | ----------------- |
| `test_plus_tab_click_emits_new_tab_requested` | `+` button click emits `new_tab_requested` |
| `test_plus_tab_tab_bar_clicked_emits_new_tab_requested` | Fallback chrome click emits signal |
| `test_non_plus_tab_bar_clicked_does_not_emit_new_tab` | Non-plus index does not emit signal |
| `test_plus_tab_click_adds_request_tab` | Presenter adds tab; plus placeholder stays last |
| `test_plus_tab_tab_bar_clicked_adds_request_tab` | Fallback path adds tab via presenter |
| `test_plus_tab_is_last` | Plus placeholder remains trailing tab |
| `test_plus_tab_close_is_ignored` | Close on plus tab is ignored |
| `test_close_first_of_two_tabs_focuses_remaining_request_tab` | After closing first of two request tabs, focus stays on remaining request tab (not `+`) |
| `test_close_rightmost_of_two_tabs_does_not_land_on_plus` | Closing the request tab adjacent to `+` must not leave current on `+` (Qt `removeTab` next-index trap) |
| `test_close_middle_of_three_tabs_focuses_remaining_request_tab` | After closing middle of three request tabs, focus stays on a remaining request tab (not `+`) |
| `test_close_rightmost_of_three_tabs_does_not_land_on_plus` | Closing last of three request tabs (next to `+`) must not select `+` |
| `test_close_last_request_tab_focuses_replacement_not_plus` | Closing the last request tab creates a blank replacement via `add_new_tab` and focuses it (not `+`) |
| `test_close_tabs_for_request_ids_rightmost_does_not_land_on_plus` | Bulk-closing the rightmost open request tab must not leave current on `+` (PYPOST-831) |
| `test_close_tabs_for_request_ids_multiple_rightmost_does_not_land_on_plus` | Bulk-closing several rightmost open request tabs must not leave current on `+` |
| `test_next_previous_tab_hotkeys_keep_focus_on_request_tabs` | Next/Previous Tab hotkey map (`Ctrl+Tab` / `Ctrl+Shift+Tab` via `register_hotkey` + `QAction.triggered`) cycles request tabs and never focuses `+` |

Run:

```bash
make test PYTEST_ARGS="tests/test_tab_header.py tests/test_tabs_presenter.py -k 'plus_tab or land_on_plus or close_tabs_for_request_ids or close_tab' -v"
```

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

GUI integration tests in `tests/test_save_flow_integration.py` (RequestWidget menu/shortcut →
`TabsPresenter`):

| Test | Behavior verified |
| ---- | ----------------- |
| `test_save_menu_action_overwrites_existing_request` | Save menu persists overwrite and emits `request_saved` |
| `test_save_menu_action_cancelled_when_dialog_dismissed` | New request save cancelled when dialog dismissed |
| `test_save_shortcut_cancelled_on_overwrite_decline` | `Ctrl+S` cancelled when overwrite confirmation declined |
| `test_save_as_shortcut_persists_copy_with_new_id` | Save-as shortcut persists copy with new tab ID |
| `test_save_as_menu_action_cancelled_when_dialog_dismissed` | Save-as menu cancelled; tab identity unchanged |

Run:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest \
  tests/test_request_save_orchestrator.py \
  tests/test_tabs_presenter.py \
  tests/test_save_flow_integration.py \
  -k "save or save_as" -v
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
- Save handlers capture the originating tab **before** modal dialogs; post-save UI updates must
  not rely on `currentIndex()` after the dialog closes (see PYPOST-72).
- Check collection and storage files for write permissions.

### `+` button is not visible or overlaps tabs

- Confirm `RequestTabHeader.tab_bar.setExpanding(False)` is active after attach.
- Verify the plus placeholder tab exists (`plus_tab_index() >= 0`) and is the last tab.
- Check `QTabBar.setTabButton` still attaches the `+` widget on the plus tab index.

### Closing a request tab leaves focus on `+`

- Qt `removeTab` advances current to the next index; when closing the rightmost request tab
  that next index is the trailing `+`.
- Confirm `TabsPresenter._ensure_current_is_navigable` reselects via
  `navigable_tab_indices()` when current is not a request tab. Callers:
  - `close_tab` (PYPOST-824; verified for two-tab rightmost under PYPOST-825;
    verified for close-current / `handle_close_tab` under PYPOST-826)
  - `close_tabs_for_request_ids` once after the remove loop (PYPOST-831; preferred =
    left of leftmost closed index)
- Regression tests: `test_close_rightmost_of_*_does_not_land_on_plus`,
  `test_handle_close_tab_closes_current`,
  `test_close_tabs_for_request_ids_*_does_not_land_on_plus` in
  `tests/test_tabs_presenter.py`.

### `Ctrl+N` works but `+` click does nothing

- Confirm `plus_btn.clicked` is connected to `new_tab_requested` in `ensure_plus_tab()` (primary
  path for clicks on the visible `+` widget).
- Verify the embedded button exists: `tab_bar.tabButton(plus_idx, LeftSide)` returns a
  `QPushButton`.
- Fallback only: `_on_tab_bar_clicked` handles `tabBarClicked` on the plus index for chrome
  clicks outside the button — not sufficient alone when users click the embedded widget.
- Verify `handle_new_tab("plus_button")` still calls `add_new_tab()` (not an early return path).

### New-tab metrics are missing

- Ensure `gui_new_tab_actions_total` is registered in `MetricsManager._init_metrics()`.
- Trigger at least one `Ctrl+N` and one `+` click before checking `/metrics`.
