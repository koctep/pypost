# Environments Dialog

## Overview
The `EnvironmentDialog` class provides the UI for managing environments in PyPost. It allows users to add, delete, and copy environments, as well as modify environment variables and toggle MCP (Model Context Protocol) settings.

## Architecture

User-visible strings (dialog titles, labels, menu actions, validation messages) live in
`pypost/core/environment_messages.py`. UI widgets and `environment_ops.validate_environment_rename`
import constants and small formatter helpers from that module.

`EnvironmentDialog` composes two widgets under `pypost/ui/widgets/environments/`:

- **`EnvironmentListWidget`**: Left pane — `QListWidget`, Add button, F2/context-menu
  rename, copy, and delete. Emits `environment_selected(int)` when the current row changes.
- **`EnvironmentVariablesWidget`**: Right pane — variables `QTableWidget` (Variable / Value /
  Hidden columns) and the MCP checkbox. Loads via `load_environment(Environment | None)` when
  the selection changes.

`EnvPresenter._open_env_manager` passes presenter-owned environments, opens the dialog, then
assigns `self._environments = dialog.environments` before saving — the presenter owns state.

### EnvPresenter public API (PYPOST-68)

`EnvPresenter` exposes `widget` for top-bar layout only. Internal combo/button/label widgets
are not public properties. Callers use:

- `apply_settings(settings)` — stores presenter settings (font via global QSS + app font)
- `select_environment_index(index)` — user intent to change active environment
- `environment_at(index)`, `current_environment_index()`, `environment_count()` — query API
- `mcp_status_text()`, `mcp_tools_button_text()`, `mcp_activity_button_text()` — MCP bar labels

Legacy attributes on `EnvironmentDialog` (`env_list`, `vars_table`, `mcp_check`) delegate to
the child widgets for tests and gradual migration.

## User-visible strings

All Manage Environments copy (window title, button labels, context-menu actions, table
headers, MCP checkbox, validation and confirmation messages) lives in
`pypost/core/environment_messages.py`. Widgets and `collection_item_dialogs` environment
helpers import from that module; rename validation in `environment_ops` uses the same
messages for consistency.

## API / Usage

### `EnvironmentDialog(environments, parent, current_env_name, log_hidden_key_names)`
Initializes the dialog.
- **environments**: List of `Environment` objects to edit. The dialog deep-copies this list
  internally; callers read results via the `environments` property after `exec()`.
- **parent**: The parent widget.
- **current_env_name**: The name of the environment currently active in the application.
- **log_hidden_key_names**: Configuration for logging hidden key names.

#### Initial synchronization & selection lifecycle (PYPOST-1073)

Upon initialization, `EnvironmentDialog` connects `EnvironmentListWidget.environment_selected` to `self.on_env_selected` and immediately triggers `self.on_env_selected(self.env_list.currentRow())`. This guarantees that:
- When opened with an active environment name, the active environment is selected in the list and its variables and MCP settings are immediately populated in the variables table.
- When opened with no environment specified (`current_env_name=None`), the first available environment (row 0) is selected and loaded into the variables table. If the list is empty, the table remains cleared (0 rows) and disabled.
- Any list mutation (`load_list`, `add_environment`, `delete_environment`) in `EnvironmentListWidget` explicitly emits `environment_selected(self.env_list.currentRow())` to prevent stale variable views when list indices are reused.


### Context Menu Actions (Environment List)
Instead of main UI buttons, actions on existing environments are handled via a right-click context menu on the `env_list`:
- **Rename**: Triggered via `_on_env_list_context_menu` or the `F2` hotkey, it calls `_rename_environment_at_row(row)` to trigger inline editing of the list item. The `itemChanged` signal handles validation and updates the selected environment.
- **Copy**: Triggered via `_on_env_list_context_menu`, it calls `_duplicate_environment_at_row(row)` to create a clone of the selected environment, prompting for a new name.
- **Delete**: Triggered via `_on_env_list_context_menu`, it calls `delete_environment(row)` to remove the selected environment from the list and data model.

### Context Menu Actions (Variables Table)
- **Move Up / Move Down**: Right-clicking a populated variable row allows users to change its relative order in the table using `_move_variable_at_row(row, direction)`. This swaps adjacent items in the ordered `Environment.variables` dict and reloads the table.
- **Delete**: Right-clicking a variable row opens a context menu to delete that specific variable using `_delete_variable_at_row(row)`.

### Variable Editing
- **`on_var_changed(item)`**: Updates the underlying `Environment` object when a user modifies the table. Automatically adds an empty row at the bottom for new variables.
- **Variable name validation**: Keys are trimmed and validated via
  `validate_environment_variable_name` (shared Jinja2-compatible rules). Invalid names are not
  saved; the Variable cell reverts to the previous value (or empty for a new row) and
  `show_invalid_variable_name_error` displays the validator message.
- **`_on_hidden_toggled(checked)`**: Manages the masking and unmasking of hidden variable values in the UI, ensuring the real value is preserved in the item's `UserRole` data.

#### Row-update helpers (`EnvironmentVariablesWidget`, PYPOST-449)

Row-level transitions are decomposed into private helpers so `on_var_changed` and hidden-toggle
paths stay readable:

| Helper | Role |
| --- | --- |
| `_is_edited_cell` | True when the `itemChanged` callback targets a given row/column |
| `_revert_invalid_variable_key` | Revert Variable cell and show validation error |
| `_resolve_hidden_value_on_edit` | Persist typed value for hidden rows and re-apply `HIDDEN_MASK` |
| `_refresh_value_cell_for_hidden_toggle` | Swap mask/plaintext when the Hidden checkbox toggles |

Value storage still uses `_make_value_item` / `_extract_real_value` (PYPOST-437). Model sync runs
through `_sync_env_variables_from_table`.

Widget-focused tests: `tests/test_environment_variables_widget.py`. Full dialog regression:
`tests/test_env_dialog.py`.

## Import environments (PYPOST-986)

`EnvironmentListWidget` gains an **Import…** button (`BUTTON_IMPORT`,
`ENV_IMPORT_BUTTON` widget id) next to **Add**, wired to
`import_environments()`. All decision logic is pure and lives outside Qt in
`pypost/core/environment_import.py`:

- `load_import_candidates(path, storage)` — reads a JSON file (single object
  or list of objects), delegates per-record decrypt/validate to the existing
  `StorageManager.deserialize_environment_records`, and returns
  `(candidates, parse_errors)`. Raises `EnvironmentImportFileError` only for
  file-level problems (unreadable, malformed JSON, wrong root shape); a
  per-record failure (e.g. an undecryptable Hidden value) is reported via
  `parse_errors` instead, so one bad entry never blocks the rest of the file.
- `find_conflicts(existing, incoming)` — names present in both lists.
- `generate_import_copy_name(name, existing_names)` — `"Copy of X"`, then
  `"Copy of X (2)"`, `"(3)"`, ... extending `format_copy_of_name` to the
  no-prompt case.
- `plan_import(existing, incoming, decisions)` — pure function returning an
  `ImportPlanResult` (`environments`, `added`, `updated`, `skipped`,
  `renamed`, `parse_errors`). `renamed` is `list[tuple[str, str]]` — one
  `(original_name, new_name)` pair per rename event (Keep Both or in-file
  duplicate), in plan order — not a `dict[str, str]`, so several incoming
  records that share a name all appear in the summary (PYPOST-1003).
  `OVERWRITE` preserves the existing environment's `id` and list position
  (adopts incoming `variables`/`hidden_keys`/`enable_mcp`) so
  `settings.last_environment_id` and the encryption-envelope reuse cache
  (`EnvironmentVariablesAdapter._persisted_variables`, keyed by `id`) are not
  invalidated. `KEEP_BOTH` appends a renamed clone (fresh id) via
  `clone_environment`. Duplicate names *within* the incoming file itself are
  always treated like `KEEP_BOTH`, with no prompt.
- `format_import_result(result)` — pure formatter for the summary dialog
  (`len(result.renamed)` for the Renamed count; iterates every pair),
  mirroring `format_migration_report` in `encryption_migration.py`.

`EnvironmentListWidget.import_environments()` orchestrates: file picker
(`prompt_import_environments_file`) → `read_import_file` callable (injected
by `EnvPresenter`, not a direct `StorageInterface` dependency — same pattern
as the existing `get_current_env_name`/`set_current_env_name` callables) →
zero-candidates guard (treated identically to a hard parse failure) →
`_resolve_import_conflicts()` prompts `prompt_import_conflict` per
conflicting name (with an "apply to all remaining conflicts" shortcut) →
`plan_import` → `self.environments[:] = result.environments` → `load_list()`
→ `format_import_result` → `show_import_result`. New dialogs
(`prompt_import_environments_file`, `show_import_invalid_file_error`,
`prompt_import_conflict`, `show_import_result`) follow the existing
`confirm_*`/`show_*` conventions in `collection_item_dialogs.py`; their
strings live in `environment_messages.py` (`BUTTON_IMPORT`,
`IMPORT_FILE_DIALOG_CAPTION`/`FILTER`, `MSG_IMPORT_*`).

No change to `StorageInterface`, the on-disk `environments.json` shape, or
encryption behavior: import only needs to carry `hidden_keys` through
correctly, and the unchanged `save_environments()` re-encrypts per the
installation's current encryption setting on the next save, exactly as it
does for hand-entered values. See `ai-tasks/PYPOST-986/20-architecture.md`
for the full design and Q&A, and `doc/user/environments.md` § Import
environments for the end-user-facing description of the file format and
conflict policy.

Tests: `tests/test_environment_import.py` (pure logic, no Qt) and
`tests/test_environment_list_widget.py::TestImportEnvironments` (Qt-level,
happy path, cancel, invalid file, zero-candidates, single conflict, "apply
to all", partial-parse success, no-op without `read_import_file`, and the
`environment_import_completed` log line). PYPOST-999 adds
`test_overwrite_import_reuses_unchanged_and_reencrypts_changed_hidden` in
`test_environment_import.py`: Overwrite `plan_import` → `save_environments`
→ on-disk envelope equality for unchanged Hidden / fresh envelope for
changed Hidden → `load_environments` (see also
`doc/dev/environment_encryption_at_rest.md` § Overwrite import × selective
re-encrypt). PYPOST-1000 locks presenter wiring in
`tests/test_env_presenter.py::test_open_env_manager_passes_working_read_import_file`:
`_open_env_manager` must pass a `read_import_file` that, against standard
`FakeStorageManager` with native plaintext deserialize (PYPOST-1060), loads
candidates from a temp JSON file (same patch-`EnvironmentDialog` style as
PYPOST-1008's invoke lock
`test_open_env_manager_passes_working_serialize_export_records`). PYPOST-1001
adds a click-level wiring lock, distinct from the direct-call tests above:
`test_environment_list_widget.py::TestImportButtonWiring::test_mouse_click_on_import_button_starts_import`
finds the **Import…** button (`findChild(QPushButton, ENV_IMPORT_BUTTON)`),
simulates a real `QTest.mouseClick`, and asserts the patched
`import_environments` was invoked — proving the button is actually connected,
not just that the action works when called directly. Verified against
current code with zero production changes (the button was already wired
correctly at `EnvironmentListWidget.__init__`). PYPOST-1002 closes two
remaining coverage gaps at the 3+-conflict boundary:
`test_environment_list_widget.py::TestImportEnvironments::test_apply_to_all_conflicts_applies_to_third_and_later_conflicts`
locks that "apply to all" (once set on the first conflict) carries through a
third and later conflict, not just a second, and
`test_environment_import.py::TestGenerateImportCopyName::test_returns_next_numbered_copy_when_first_two_taken`
locks `generate_import_copy_name` advancing past `"Copy of X (2)"` to
`"Copy of X (3)"` when both are already taken. Both were verification locks
against existing, already-correct logic — no production code changed.

## Export environments (PYPOST-988)

`EnvironmentListWidget` gains an **Export…** button (`BUTTON_EXPORT`,
`ENV_EXPORT_BUTTON` widget id) beside **Import…**, wired to
`export_environments()`. Pure logic lives in
`pypost/core/environment_export.py`:

- `ExportScope` — `SELECTED` or `ALL`.
- `environments_for_export(all_environments, scope, selected_index)` —
  resolves which in-memory environments to write.
- `export_includes_hidden(environments)` — true when any target has
  `hidden_keys`.
- `build_export_payload(environments, storage)` — calls the new
  `StorageManager.serialize_environment_records` (native on-disk JSON shape,
  including encrypted envelopes when encryption is enabled).
- `write_export_file(path, payload)` — delegates to the shared
  `pypost/core/export_file_writer.py::write_json_export_file(path, payload, *,
  error_cls)` helper (PYPOST-1011, also used by collection export): creates
  `path`'s parent directories, writes indented UTF-8 JSON with a trailing
  newline, and wraps any `(OSError, TypeError, ValueError)` as
  `EnvironmentExportError` on write failure.
- `format_export_result(ExportPlanResult)` — summary dialog text.

**Hidden/secrets policy:** values are **included, not redacted**, with a
mandatory `confirm_export_includes_secrets` warning when any exported
environment has Hidden variables — see `doc/user/environments.md` § Hidden
values in export files.

`EnvironmentListWidget.export_environments()` orchestrates: scope prompt
(`prompt_export_scope`) → selected-row guard → secrets confirmation (if
needed) → save dialog (`prompt_export_environments_file`) → injected
`serialize_export_records` callable → `write_export_file` →
`show_export_result`. `EnvPresenter._open_env_manager` wires
`serialize_export_records=self._storage.serialize_environment_records`
(bound method, not a wrapping lambda).

Export does not mutate the working list or touch disk except for the chosen
export path. The [shared JSON root policy](json_export_root.md) selects one
JSON object for exactly one environment and an array for zero or multiple
environments; both shapes are accepted by import (PYPOST-986). The injected
widget serializer and the core `build_export_payload` path both apply the
same helper after serialization.

Tests: `tests/test_environment_export.py` (pure logic, encryption-off
round-trip with `load_import_candidates`) and
`tests/test_environment_export_ui.py` (Qt-level
scope/cancel/secrets/no-op/log coverage). PYPOST-1009 adds
`test_write_encrypted_export_file_round_trips_through_import`: encryption
on, temp key, envelope on disk, same-key re-import (see also
`doc/dev/environment_encryption_at_rest.md` § Encrypted export file
round-trip). PYPOST-1008 locks presenter wiring in
`tests/test_env_presenter.py::test_open_env_manager_passes_working_serialize_export_records`:
`_open_env_manager` must pass a `serialize_export_records` captured from the
patched `EnvironmentDialog` constructor and invoked against
`FakeStorageManager` (shared fake; plaintext environments) so it returns
export records — invoke, not identity only. Bound-method identity remains in
`test_open_env_manager_passes_storage_serializer_directly` (local
`FakeStorage`); that sibling does not replace the invoke lock.

## Configuration
N/A

## Troubleshooting
- **Hidden Values Losing Data**: Ensure that when `HIDDEN_MASK` is displayed, the real value is stored in `Qt.ItemDataRole.UserRole`. Check `_extract_real_value` and `_make_value_item` for details on how the value is preserved.
- **Duplicate Environment Names**: When copying an environment, the UI validates that the new name is not empty and does not already exist, prompting the user again if invalid.
- **Import "Renamed" undercount**: If the summary Renamed count is lower than the
  number of `Copy of …` names after import, confirm `ImportPlanResult.renamed` is
  `list[tuple[str, str]]` (PYPOST-1003). n same-named duplicates report n−1 renames.

## Testing

Automated Qt/offscreen coverage lives in `tests/test_env_dialog.py` (module timeout 60s).
The suite exercises:

- Environment list selection, add/delete, and rename validation
- **Initial synchronization & selection** (PYPOST-1073): immediate variable table population on open (active env, no env fallback, empty list), reactive updates on row switching, add, and delete
- **Copy / duplicate** via `_duplicate_environment_at_row` and context-menu wiring
  (QInputDialog cancel, empty name, duplicate name — patched dialogs/message boxes)
- Variables table: hidden flags, moves, deletes, trailing add row, invalid name revert
- MCP checkbox sync and logging (`caplog` for masked vs readable hidden keys)

Run: `pytest tests/test_env_dialog.py -q`

### Test Doubles and Helpers: FakeStorageManager (PYPOST-1060)

For hermetic unit and UI tests without cryptography dependencies or temporary keyrings, `tests/helpers/__init__.py` provides `FakeStorageManager`, which implements native in-memory environment serialization and deserialization:

- **`serialize_environment_records(environments)`**: Serializes `Environment` instances to a list of dictionaries using `env.model_dump(mode="json")`.
- **`deserialize_environment_records(records)`**: Deserializes in-memory plaintext environment dictionaries into `tuple[list[Environment], tuple[EnvironmentLoadFailure, ...]]` using `Environment.model_validate(item)`.

Key characteristics:
- **Fault isolation**: If a record is malformed (e.g. invalid field types or non-mapping items), it is collected as an `EnvironmentLoadFailure(name, environment_id, reason)` without raising exceptions or aborting processing for the remaining valid records in the batch.
- **Zero encryption overhead**: Operates directly on plaintext dictionaries without requiring fake encryption keys, keyring services, or on-disk storage setup.
- **Direct test usage**: Tests such as `tests/test_env_presenter.py` and `tests/test_fake_storage_manager.py` can instantiate `FakeStorageManager()` directly to serialize and deserialize environment records instead of defining ad-hoc test double subclasses or mocking deserialization methods.

