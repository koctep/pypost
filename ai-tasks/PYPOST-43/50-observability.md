# PYPOST-43: Observability — Decompose MainWindow into Presenters

## 1. Scope

This document covers logging and metrics additions made to the presenter layer introduced in
PYPOST-43. Each gap was identified by reviewing the implementation produced by the Junior
Engineer (see `40-code-cleanup.md`).

---

## 2. Existing Observability (Before This Step)

### Already present
- All three presenter modules had `logger = logging.getLogger(__name__)` at module level.
- `CollectionsPresenter` had comprehensive `logger.*` + `MetricsManager` calls covering
  rename and delete flows (selected, cancelled, rejected_empty, not_found, error, succeeded).
- `TabsPresenter` had logging in `handle_new_tab` and the full `_handle_save_as_request` flow.
- `MetricsManager` exposed `track_request_sent` / `track_response_received` counters but
  neither was wired to the actual HTTP send path.
- `_on_script_output` was an explicit no-op stub tagged for the observability step.

### Gaps identified
| Location | Gap |
|---|---|
| `TabsPresenter._handle_send_request` | No log or metric on request dispatch / stop |
| `TabsPresenter._on_request_finished` | No log or metric on response received |
| `TabsPresenter._on_request_error` | No log on error / cancellation |
| `TabsPresenter._on_script_output` | No-op stub — script output silently dropped |
| `TabsPresenter.restore_tabs` | No log on startup restore |
| `TabsPresenter._handle_save_request` | No log or metric on save / overwrite |
| `EnvPresenter` (entire file) | Zero log statements |
| `CollectionsPresenter.load_collections` | No log on collection count |
| `CollectionsPresenter._on_collection_clicked` | No log when request opened in tab |
| `MainWindow.__init__` | No startup log |
| `MainWindow.handle_exit` | No shutdown log |
| `MainWindow.open_settings` | No log on settings change / metrics restart |

---

## 3. Changes Made

### 3.1 `pypost/ui/presenters/tabs_presenter.py`

#### `restore_tabs()`
- Log `restore_tabs_no_saved_tabs` (INFO) when no saved tabs exist and a blank tab is opened.
- Log `restore_tabs_request_not_found` (WARNING) for each saved request ID that can no
  longer be resolved (e.g. request deleted since last session).
- Log `restore_tabs_completed` (INFO) with `restored_count` on success.

#### `_handle_send_request()`
- Log `request_stop_requested` (INFO) with method + url when the user clicks Stop on an
  in-flight request.
- Log `request_send_initiated` (INFO) with method, url, request_id before dispatching the
  worker.
- Call `MetricsManager().track_request_sent(method)` — wires the existing Prometheus counter
  `requests_sent_total` to real request dispatches.

#### `_on_request_finished()`
- Log `request_finished` (INFO) with method, status_code, elapsed_time, size.
- Call `MetricsManager().track_response_received(method, str(status_code))` — wires the
  existing `responses_received_total` counter.

#### `_on_request_error()`
- Log `request_cancelled` (INFO) for aborted/cancelled requests (previously silent).
- Log `request_error` (ERROR) for genuine failures.

#### `_on_script_output()` *(was no-op stub)*
- Implemented: each line of `logs` is emitted at DEBUG level as `script_output`.
- `err` content is emitted at WARNING level as `script_error`.
- Uses `id(tab)` to correlate output to the originating tab.

#### `_handle_save_request()`
- Log `save_request_overwrite_cancelled` (INFO) when the user declines the overwrite dialog.
- Log `save_request_overwrite_succeeded` (INFO) with request_id + collection_id on overwrite.
- Call `MetricsManager().track_gui_save_action("overwrite")` on successful overwrite.
- Log `save_request_failed` (WARNING) with reason when no target collection is resolved.
- Log `save_request_new_succeeded` (INFO) with request_id, name, collection_id for new saves.
- Call `MetricsManager().track_gui_save_action("new")` on new save.

---

### 3.2 `pypost/ui/presenters/env_presenter.py`

#### `load_environments()`
- Log `load_environments_completed` (INFO) with `count`.

#### `_on_env_changed()`
- Log `env_selected` (INFO) with env_id, env_name, mcp_enabled, var_count on environment
  activation.
- Log `env_deselected` (INFO) with index when "No Environment" is chosen.

#### `on_env_update()`
- Log `env_variables_updated_from_script` (INFO) with env_id, env_name, var_count when a
  post-request script pushes variable updates.

#### `handle_variable_set_request()`
- Log `variable_set_request_no_env_selected` (WARNING) when the user attempts to set a
  variable with no environment active.
- Log `variable_set_in_env` (INFO) with env_id, env_name, key on success.

#### `_open_env_manager()`
- Log `env_manager_dialog_opened` (INFO) with `current_env` before the dialog opens.
- Log `env_manager_dialog_closed` (INFO) after the dialog closes.

#### `_on_mcp_status_changed()`
- Log `mcp_server_started` (INFO) with host + port on MCP start.
- Log `mcp_server_stopped` (INFO) on MCP stop.

---

### 3.3 `pypost/ui/presenters/collections_presenter.py`

#### `load_collections()`
- Log `load_collections_completed` (INFO) with `collection_count` and `request_count`.

#### `_on_collection_clicked()`
- Log `collection_request_opened` (INFO) with request_id + request_name when a request is
  opened in a new tab.

---

### 3.4 `pypost/ui/main_window.py`

- Log `main_window_initialized` (INFO) at the end of `__init__` after all presenters are
  ready.
- Log `main_window_exit_requested` (INFO) in `handle_exit`.
- Log `settings_applied` (INFO) with font_size + indent_size in `open_settings`.
- Log `metrics_server_restarting` (INFO) with host + port when the metrics endpoint changes.

---

## 4. Metrics Coverage After This Step

| Prometheus Counter | Label(s) | Wired From |
|---|---|---|
| `requests_sent_total` | `method` | `TabsPresenter._handle_send_request` |
| `responses_received_total` | `method`, `status_code` | `TabsPresenter._on_request_finished` |
| `gui_save_actions_total` | `source` (`new`, `overwrite`) | `TabsPresenter._handle_save_request` |
| `gui_save_as_actions_total` | `source` | `TabsPresenter._handle_save_as_request` *(pre-existing)* |
| `gui_new_tab_actions_total` | `source` | `TabsPresenter.handle_new_tab` *(pre-existing)* |
| `gui_collection_delete_actions_total` | `item_type`, `status` | `CollectionsPresenter` *(pre-existing)* |
| `gui_collection_rename_actions_total` | `item_type`, `status` | `CollectionsPresenter` *(pre-existing)* |

---

## 5. Log Level Convention

| Level | Usage in this codebase |
|---|---|
| `DEBUG` | Script output lines from post-request scripts |
| `INFO` | Normal application events (startup, request sent/finished, env changes, saves) |
| `WARNING` | Unexpected but recoverable conditions (missing target, request not found, no env) |
| `ERROR` | Failures requiring user attention (request errors, rename/delete errors) |

---

## 6. No New Dependencies

All observability additions use the Python standard library `logging` module and the existing
`MetricsManager` singleton. No new packages were introduced.
