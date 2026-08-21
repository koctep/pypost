# Collection Import

## Overview

**Import Collection** (PYPOST-987) loads one or more collections, with all of their
requests, from a JSON file into the running app. The accepted format is PyPost's own
collection serialization — a copy of a `{data_dir}/collections/{id}.json` file, or a JSON
list of such objects. Foreign formats (Postman, Insomnia, OpenAPI) are explicitly out of
scope.

It mirrors [Import environments](environments_dialog.md) (PYPOST-986) structurally: a
Qt-free core that decides everything, and a thin Qt shell that asks questions and shows
results. The domains differ enough that the code is separate — collections are stored one
file per collection rather than in a single document, and they contain nested requests
whose ids participate in a global index — but the conflict vocabulary is genuinely shared
and lives in one place.

**PYPOST-1005** moves file parse off the GUI thread so a large import does not freeze the
main window. Conflict prompts, plan, and apply still run on the GUI thread after parse
completes — same outcomes as PYPOST-987 / PYPOST-1004, with a non-modal preparing cue
while the worker runs.

**PYPOST-1058** aligns the completion summary dialog and `collection_import_completed`
log with durable storage after save failures. If any collection fails to save to disk,
`recount_collection_import_plan` adjusts Added, Updated, Renamed, and Requests Imported
totals to reflect only what successfully persisted, matching the sidebar tree.

**PYPOST-1059** establishes UI regression assertions guaranteeing that the sidebar tree
(`QTreeView` / `QStandardItemModel`) and `RequestManager.get_collections()` strictly
synchronize with durable storage after partial or total import save failures.

**PYPOST-1061** introduces optional determinate progress updates during collection import
validation. `load_collection_import_candidates` accepts an optional `on_progress(done, total)`
callback, `CollectionImportParseWorker` emits `parse_progress(int, int)` (with alias `progress`),
and `CollectionImportActions` updates the status bar with `MSG_IMPORT_VALIDATING`
("Validating collections ({done}/{total})…") while parsing and validating candidate records.

**PYPOST-1062** profiles collection import planning (`plan_collection_import`) and application
(`apply_imported_collections`) under large synthetic datasets (500 collections, 2,500 requests).
Profiling confirmed that in-memory planning executes in ~20ms (< 100ms budget) and batch persistence
executes with minimal latency, validating that keeping plan/apply on the GUI thread avoids unnecessary
threading complexity while maintaining interactive responsiveness. Automated benchmarks reside in
`tests/test_collection_import_profile.py`.

## Architecture

```text
CollectionsPresenter.panel          Import Collection… button (COLLECTION_IMPORT_BUTTON)
        │
        ▼  delegates
CollectionImportActions (QObject)   pick → async parse → prompt → plan → apply → refresh
        │
        ├─ CollectionImportParseWorker  QThread: read_import_file(path)
        ├─ Busy cue                     status bar + Import button disabled
        ├─ collection_item_dialogs      QFileDialog + conflict / invalid / result boxes
        ├─ collection_import            pure: parse, conflicts, id reservation, plan, summary
        └─ collection_import_apply      RequestManager swap + StorageManager writes
```

```text
Before (UI thread, pre-PYPOST-1005):
  pick → PARSE (blocks) → conflicts → plan → apply → result

After:
  pick → PARSE worker (background) + busy cue
       → conflicts → plan → apply → result   (GUI thread, unchanged)
```

- **`pypost/core/collection_import.py`** — the pure core. No Qt, no storage. Parses a
  file into candidate `Collection` models, detects name conflicts, reserves colliding
  ids, computes the resulting collection list, recounts plan results against save
  failures (`recount_collection_import_plan`), and formats the summary text. Directly
  unit-testable without a `QApplication` or a data directory. Called from the parse
  worker via the injected `read_import_file` callable (default
  `load_collection_import_candidates`).
- **`pypost/core/qt/collection_import_parse_worker.py`** —
  `CollectionImportParseWorker` (`QThread`). Runs `read_import_file(path)` off the GUI
  thread; emits `parse_completed(collections, parse_errors)` or `parse_failed(error)`.
  No widget access. Same one-shot worker shape as `PasteJsonFormatWorker` /
  `CollectionStorageWorker` — not a reuse of `CollectionStorageGateway` (different I/O:
  user-chosen file vs data-dir load).
- **`pypost/core/collection_messages.py`** — every user-visible string (dialog titles,
  file filter, button label, summary lines, per-record error reasons, and
  `MSG_IMPORT_PREPARING` for the status-bar cue), mirroring `environment_messages.py`.
- **`pypost/core/import_conflicts.py`** — `ImportConflictDecision` and
  `generate_import_copy_name`, extracted from `environment_import.py` so both import
  flows share one conflict vocabulary. `environment_import.py` re-exports them, so no
  environment-side call site changed.
- **`pypost/core/collection_import_apply.py`** — `apply_imported_collections`, the only
  bulk collection-write loop in the codebase. A free function over `RequestManager`'s
  public surface rather than a method on it, which keeps `request_manager.py` inside its
  SOLID audit cap (`scripts/audit_baseline_metrics.py`). Returns
  `CollectionImportApplyResult` containing formatted failure messages and failed collection
  IDs.
- **`pypost/ui/presenters/collection_import_actions.py`** — `CollectionImportActions`,
  a `QObject` orchestrator. Owns worker lifecycle and busy state; sequences pick →
  async parse → sync conflict/plan/apply/result. Split out of `CollectionsPresenter`
  the same way `CollectionTreeActions` and `CollectionsAsyncLoader` are.
- **`pypost/ui/collection_item_dialogs.py`** — four helpers:
  `prompt_import_collection_file`, `show_collection_import_invalid_file_error`,
  `prompt_collection_import_conflict`, `show_collection_import_result`. The
  Overwrite/Keep Both/Skip message box body is shared with the environment flow through
  the private `_prompt_import_conflict_box`. Dialogs run only on the GUI thread after
  parse completes.
- **`pypost/ui/presenters/collections_presenter.py`** — gained a `panel` property. The
  sidebar tab now mounts `presenter.panel` (a `QWidget` holding the tree plus an action
  row) instead of the bare tree; `presenter.widget` still returns the `QTreeView`, so
  existing callers and automation are unaffected. Injects status-bar show/clear hooks
  for the preparing cue; keeps the optional `read_import_file` DI seam.

### Async parse and busy cue (PYPOST-1005)

1. User clicks **Import Collection…**; `import_collections` returns immediately if
   `is_busy()` (second click while preparing is skipped — log-and-return, not queued).
2. File picker runs on the GUI thread (unchanged).
3. Orchestrator shows the initial busy cue and starts `CollectionImportParseWorker`:
   - Status bar: `MSG_IMPORT_PREPARING` (“Preparing collection import…”), transitioning
     to `MSG_IMPORT_VALIDATING` (“Validating collections ({done}/{total})…”) as
     `parse_progress(done, total)` signals arrive from the worker.
   - Import button (`COLLECTION_IMPORT_BUTTON`) disabled via `findChild` on the panel.
4. Worker runs `read_import_file` off-thread; emits completed or failed.
5. Orchestrator clears the cue, then on the GUI thread either shows the invalid-file
   dialog or runs conflict prompts → `plan_collection_import` →
   `apply_imported_collections` → refresh → result dialog.
6. Worker `finished` slot: `deleteLater` + bounded `wait(100)` (PYPOST-829 hygiene;
   WARNING if the short join times out).

There is no modal `QProgressDialog` and no determinate percent bar — same class of
experience as [Collection Loading](collection_loading.md) startup async load, plus a
visible preparing cue for a user-initiated action. Plan and apply remain synchronous
after parse; only parse is off-thread.

### Plan-then-apply

`plan_collection_import` is pure and touches nothing — it returns both the complete
target list and the subset that must be written. `apply_imported_collections` then swaps
the in-memory list and writes only that subset. A collection the user skipped appears in
neither list, so its stored file is never rewritten.

This split is what makes "invalid file changes nothing" cheap to guarantee: the failure
paths all return before any planning happens, and planning itself cannot mutate state
even if it did run.

### Conflict policy

Only **name** conflicts are surfaced to the user, per name, with an "apply to all
remaining conflicts" checkbox:

- **Overwrite** — the existing collection keeps its `id`, `name`, and position in the
  tree; its requests are replaced wholesale by the imported ones. Preserving identity
  keeps tree state and any id-keyed references intact.
- **Keep Both** — added as `Copy of <name>`, disambiguated to `Copy of <name> (2)`,
  `(3)`, … via `generate_import_copy_name`.
- **Skip** — nothing changes, and the stored file is not touched.

Duplicate names *within the imported file itself* are always renamed like Keep Both, with
no prompt: neither duplicate is a collection the user already had locally to protect.
Each such rename is recorded as one `(original, new_name)` pair on the plan result (see
`renamed` below), so three same-named entries report two renames, not one.

**Id** collisions are resolved silently, because they are data-integrity repairs rather
than user decisions:

- A colliding **collection** id would make `save_collection` overwrite an unrelated
  collection's file, since the filename is `{collection.id}.json`.
- A colliding **request** id would shadow an existing entry in
  `RequestManager._request_index` and silently break open/rename/delete for it.

A free id is always preserved, so copying a `collections/<id>.json` onto a clean machine
restores faithfully. On Overwrite, the replaced collection's request ids are released
back into the pool first, so re-importing the same file repeatedly keeps request ids
stable.

### Error isolation

File-level problems raise `CollectionImportFileError` and abort the whole import:
unreadable file, malformed JSON, a root that is neither a list nor an object, or a list
element that is not an object. Per-record problems are collected into a `parse_errors`
list instead, so one bad entry never blocks its valid siblings; they are reported by name
in the summary dialog.

Every `Collection` field has a default, so `Collection(**{"anything": 1})` would validate
into a nameless empty placeholder. `_shape_error` therefore requires a non-blank `name`
and a list-shaped `requests` *before* handing the record to Pydantic — that is what turns
a foreign-tool file into a named parse error rather than a phantom empty collection in the
tree.

## API / Usage

### `load_collection_import_candidates(path) -> (list[Collection], list[str])`

Reads and parses an import file. A single JSON object is normalized to a one-item list.

- **path**: `Path` to the file to read.
- **Returns**: candidate collections, and one formatted message per rejected record.
- **Raises**: `CollectionImportFileError` for file-level problems only.

### `find_collection_conflicts(existing, incoming) -> list[str]`

Names present in both lists, in incoming order, without duplicates. Drives how many times
the conflict prompt is shown.

### `plan_collection_import(existing, incoming, decisions) -> CollectionImportPlanResult`

Applies `decisions` (`{name: ImportConflictDecision}`) and returns the plan. Pure: neither
input list is mutated. A name absent from `decisions` defaults to `SKIP`.

`CollectionImportPlanResult` carries `collections` (the complete target list), `persisted`
(the subset to write), `added` / `updated` / `skipped` / `renamed`, `request_count`, and
`parse_errors`.

`renamed` is `list[tuple[str, str]]` — one `(original_name, new_name)` pair per rename
event (Keep Both or in-file duplicate), in plan order. It is intentionally not a
`dict[str, str]`: several incoming records can share the same original name, and a dict
keyed by that name would keep only the last pair (PYPOST-1003). Downstream UI only uses
`len(result.renamed)` and truthiness; formatters iterate the pairs directly.

### `format_collection_import_result(result) -> str`

Human-readable summary for the result dialog: counts (`len(result.renamed)` for the
Renamed line), every `"original" -> "new_name"` pair from `result.renamed`, and any
per-entry failures.

### `recount_collection_import_plan(plan, failed_ids) -> CollectionImportPlanResult`

Pure function adjusting import plan metrics when save failures occur (PYPOST-1058):

- **plan**: The original `CollectionImportPlanResult` computed by `plan_collection_import`.
- **failed_ids**: `set[str]` of collection IDs that failed during `save_collection`.
- **Returns**: A new `CollectionImportPlanResult` where failed collections are removed from
  `added`, `updated`, and `renamed` (both count and `(orig, new_name)` detail pairs), and
  `request_count` sums only the requests of successfully persisted collections. `skipped`
  and `parse_errors` are preserved.
- When `failed_ids` is empty (happy path), returns `plan` directly with zero overhead.

### `apply_imported_collections(manager, collections, persisted) -> CollectionImportApplyResult`

Swaps in the planned list via `RequestManager.apply_loaded_collections` (which rebuilds
`_request_index`) and writes each collection in `persisted`. Returns a
`CollectionImportApplyResult` containing `failures: list[str]` (formatted error strings)
and `failed_ids: set[str]` (IDs of collections that failed to save). The loop continues
past a failure so one bad write cannot strand the rest.

`CollectionImportApplyResult` implements Python's sequence protocol (`__iter__`,
`__len__`, `__getitem__`, `__bool__`, and `__eq__` with `list[str]`), maintaining full
backwards compatibility for callers and tests that treat the return value as a list of
failure messages.

If any write raises `OSError`, the function calls `manager.reload_collections()` before
returning so in-memory collections and `_request_index` match durable storage
(PYPOST-1004). Successful sibling writes stay on disk and remain visible after reload;
failed ones are absent or revert to the previous on-disk file. When every write succeeds,
there is no reload.

Deliberately **not** routed through `RequestManager.create_collection`, which rejects
duplicate names: an import resolves name conflicts through an explicit user decision and
may legitimately produce a name `create_collection` would refuse.

### Result dialog and logging after save failure (PYPOST-1058)

When `apply_imported_collections` returns with save failures (`failed_ids` is non-empty),
`CollectionImportActions` invokes `recount_collection_import_plan(result, apply_result.failed_ids)`
before appending the save failure messages to `result.parse_errors`.

The result summary dialog and the `collection_import_completed` log event reflect the
**durable outcome** rather than pre-save plan counts:
- Failed additions are excluded from `added` and reported as 0 Added.
- Failed overwrites are excluded from `updated` and reported as 0 Updated.
- Failed conflict copies / in-file renames are excluded from `renamed` count and the
  `"original" -> "new_name"` detail section.
- `request_count` includes only requests belonging to successfully persisted collections.
- `save_errors` are listed under the errors section.
- `success=False` is set whenever save failures occur.

This ensures the completion dialog, log events, and sidebar tree all truthfully agree on
what persisted to disk.

### UI sidebar tree model synchronization after save failure (PYPOST-1059)

When `apply_imported_collections` completes—regardless of whether all collections saved or
some/all failed—`CollectionImportActions._finish_import` unconditionally triggers
`self._refresh_tree()` before displaying the result dialog.

The synchronization guarantee works as follows:
1. **Apply & Reconcile**: If any write raises `OSError`, `apply_imported_collections`
   invokes `RequestManager.reload_collections()`, reloading memory and index state from
   `StorageManager.load_collections()`.
2. **Model Rebuild**: `_refresh_tree()` calls `CollectionsPresenter.refresh_tree()`, which
   clears the underlying `QStandardItemModel` and rebuilds the `QTreeView` hierarchy from
   `RequestManager.get_collections()`.
3. **Consistency**:
   - Each successfully persisted collection appears as a top-level `QStandardItem` with its
     child request items (`{method} {name}`).
   - Collections that failed to save are never rendered in the tree model (or revert to their
     prior durable on-disk state if an overwrite failed).
   - Pre-existing collections that were not part of the import remain intact.
4. **State Restoration**: `self._restore_tree_state()` and `self._emit_collections_changed()`
   ensure selection, expansion state, and downstream listeners (e.g. MCP endpoints) reflect
   the durable collection set.

### `CollectionImportParseWorker`

Background `QThread` that calls the injected `read_import_file(path)` and emits:

- `parse_completed` — `(list[Collection], list[str])` candidates and per-record errors
- `parse_failed` — `CollectionImportFileError` or an unexpected `Exception`

Workers are one-shot. On `finished`, `CollectionImportActions` schedules `deleteLater`
and a short `wait(100)` before dropping the reference (same PYPOST-829 pattern as
[Collection Loading](collection_loading.md) / [Async Environment Storage](environment_storage_async.md)).

### `CollectionImportActions`

`QObject` owned by the presenter. Public surface:

- **`is_busy() -> bool`** — true while preparing / the parse worker is running. Second
  Import click while busy is ignored (`collection_import_skipped reason=busy`).
- **`import_collections() -> None`** — pick file; dispatch async parse; finish on the
  GUI thread when ready. Callers and the button wire-up do not change.

Constructor DI (beyond the original refresh/emit hooks): optional `show_status` /
`clear_status` for the preparing message; `read_import_file` for the worker.

### Testing seam

`CollectionsPresenter.__init__` accepts an optional `read_import_file` callable,
defaulting to `load_collection_import_candidates`. Qt tests inject a stub reader to
exercise the flow without touching disk; the end-to-end test omits it and drives the real
parser, `RequestManager`, and `StorageManager` against a `tmp_path`.

Because parse is async, UI tests must wait for completion (e.g. `process_until` until
`not actions.is_busy()` or equivalent) rather than asserting immediately after
`import_collections()`. Stubs used from the worker thread must be thread-safe.

Responsiveness coverage: `tests/test_collection_import_responsiveness.py` injects a
blocking reader and asserts the Qt event loop still fires a `QTimer` during parse, with
the busy cue observable. Semantic cases live in `tests/test_collections_import_ui.py`
with async waiters.

PYPOST-1006 (verification debt; no product change) adds three locks:

- **Invalid-file logs** (`tests/test_collections_import_ui.py`):
  `test_logs_file_invalid_on_parse_failure` and
  `test_logs_file_invalid_on_zero_usable_collections`. Both
  `collection_import_file_invalid` `reason`s via `caplog` on
  `pypost.ui.presenters.collection_import_actions` (not the worker).
  Parse failure: `reason=` plus the exception text, and no
  `reason=no_valid_collections`. Empty candidates: exact token
  `reason=no_valid_collections`. Same `_wait_import` as the dialog.
- **Apply-to-all 3+** (`tests/test_collections_import_ui.py`
  `test_apply_to_all_prompts_only_once_for_three_conflicts`): three
  distinct conflicting names, KEEP_BOTH + apply-to-all, one prompt
  (`remaining_count=2`) and three `Copy of …` names. KEEP_BOTH (not
  SKIP) is required: a missing decision defaults to SKIP, so SKIP cannot
  prove the loop recorded the third name.
- **Copy name past `(2)`** (`tests/test_collection_import.py`
  `test_keep_both_uses_next_numbered_copy_when_copy_and_copy_2_taken`):
  `plan_collection_import` KEEP_BOTH when `Copy of API` and
  `Copy of API (2)` are already taken yields unique `Copy of API (3)`.

### UI storage reconciliation regression coverage (PYPOST-1059)

To ensure the UI sidebar never presents ghost or unsaved collections after I/O errors,
`tests/test_collections_import_ui.py` contains regression tests verifying tree model
synchronization against durable storage:

- **Partial save failure (`TestImportCollections.test_partial_save_failure_tree_and_manager_match_durable_storage`)**:
  Simulates a multi-collection import where one collection succeeds and another fails with
  `OSError("disk full")`. Asserts that `manager.get_collections()` and
  `presenter.widget.model()` (`QStandardItemModel`) contain only the pre-existing and
  successfully persisted collections (`rowCount() == 2`), with zero ghost rows for the failed
  collection.
- **Total save failure (`TestImportCollections.test_total_save_failure_retains_only_preexisting_durable_collections`)**:
  Simulates an import where all collection writes raise `OSError("permission denied")`.
  Asserts that `manager.get_collections()` and `presenter.widget.model()` strictly retain only
  the pre-existing collection (`rowCount() == 1`), leaving the tree unaltered.
- **End-to-end real storage failure (`TestImportCollectionsEndToEnd.test_real_storage_save_failure_reconciles_tree_and_disk`)**:
  Drives a real `StorageManager` in `tmp_path`, real `RequestManager`, and `CollectionsPresenter`.
  Monkeypatches a save error on a secondary collection in a multi-collection file. Asserts that
  actual on-disk files (`StorageManager.load_collections()`), in-memory state
  (`manager.get_collections()`), and the rendered `QTreeView` hierarchy (top-level collection
  rows and child request items) strictly match the durably saved state.

## Configuration

None. No new setting, environment variable, on-disk format, `StorageInterface` method, or
third-party dependency was introduced. The file-dialog filter, caption, and preparing
status text are constants in `collection_messages.py`.

## Observability

Structured `key=value` lines. Names, URLs, headers, bodies, scripts, full candidate
lists, and the status-bar string itself are never logged — an imported collection
routinely carries credentials in a header template. Paths are logged for triage
(user-chosen import file). See `ai-tasks/PYPOST-987/50-observability.md`,
`ai-tasks/PYPOST-1004/50-observability.md`,
`ai-tasks/PYPOST-1005/50-observability.md`,
`ai-tasks/PYPOST-1006/50-observability.md`,
`ai-tasks/PYPOST-1058/50-observability.md`, and
`ai-tasks/PYPOST-1059/50-observability.md`.

### Async parse lifecycle (PYPOST-1005)

In `collection_import_actions.py`:

- **INFO** `collection_import_skipped reason=busy` — second Import while preparing
- **INFO** `collection_import_parse_started path=…` — orchestrator dispatched the worker
- **DEBUG** `collection_import_busy_cue_shown` / `collection_import_busy_cue_cleared`
- **ERROR** `collection_import_parse_unexpected error=…` — unexpected exception from the
  worker, handled on the GUI thread (invalid-file dialog)
- **WARNING** `collection_import_worker_finish_wait_timeout wait_ms=…` — short join after
  `QThread.finished` did not complete

In `collection_import_parse_worker.py`:

- **DEBUG** `collection_import_parse_worker_started path=…`
- **DEBUG** `collection_import_parse_worker_completed path=… count=… error_count=…`
- **WARNING** `collection_import_parse_worker_failed path=… reason=…` —
  `CollectionImportFileError`
- **ERROR** `collection_import_parse_worker_failed path=… error=…` — unexpected exception
  (`exc_info=True`)

Happy-path operator order (INFO/default): `collection_import_parse_started` → (core
`collection_import_file_parsed` when using the real loader) → apply lines →
`collection_import_completed`. Enable DEBUG to confirm busy-cue show/clear and worker
start/complete around that span.

File-level failures are logged twice on purpose: worker WARNING/ERROR confirms
off-thread failure; orchestrator then emits the terminal
`collection_import_file_invalid` “nothing changed” event used since PYPOST-987.

PYPOST-1006 asserts both orchestrator `reason`s via `caplog` in
`tests/test_collections_import_ui.py` (`test_logs_file_invalid_on_parse_failure`
and `test_logs_file_invalid_on_zero_usable_collections`). Tests must not treat
worker `collection_import_parse_worker_failed` as the terminal event.
Zero-usable-collections is not a worker failure: parse returns `[]`, and only
the orchestrator emits `reason=no_valid_collections`.

### Parse / apply / completion (PYPOST-987 / PYPOST-1004 / PYPOST-1058)

In `collection_import.py`:

- **INFO** `collection_import_file_parsed path=… candidate_count=… error_count=…`

In `collection_import_actions.py`:

- **WARNING** `collection_import_file_invalid reason=…` — the exception message, or the
  literal `no_valid_collections` (both reasons locked via caplog, PYPOST-1006)
- **INFO** `collection_import_completed added_count=… updated_count=… skipped_count=…
  renamed_count=… request_count=… error_count=…` — counts reflect the durable
  outcome after `recount_collection_import_plan` (PYPOST-1058) when save failures occur

In `collection_import_apply.py`:

- **INFO** `collection_import_applied collection_count=… persisted_count=…
  failed_count=…` — `collection_count` is the **planned** list length passed into
  apply (pre-reconcile), not the post-reload size
- **ERROR** `collection_import_save_failed collection_id=… error=…` — one per
  failed write
- **WARNING** `collection_import_reconciled failed_count=… collection_count=…` —
  emitted only after `reload_collections()` when save failures are non-empty;
  `collection_count` is the post-reload in-memory size (durable-aligned). Absent
  on the happy path

Operator reading order on mid-write failure: ERROR `collection_import_save_failed`
(one or more), then WARNING `collection_import_reconciled`, then INFO
`collection_import_applied` with `failed_count > 0`, then INFO
`collection_import_completed` with `error_count > 0` (UI). The failed-write line logs
the collection id, not its name.

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Window freezes while importing a large file | Pre-PYPOST-1005 synchronous parse on the GUI thread, or a pathological plan/apply hitch after a fast parse | Confirm you are on a build with `CollectionImportParseWorker`; during prepare the status bar should show “Preparing collection import…” and Import should stay disabled while the window remains interactive |
| Second Import click does nothing while preparing | Busy re-entry guard (`is_busy`); click is not queued | Wait for the preparing cue to clear, then click again; look for INFO `collection_import_skipped reason=busy` |
| "No valid collections found in this file." | The file parsed, but every entry was rejected — most often a foreign format whose root object has no top-level `name` | Check the per-entry reasons listed below the message in the same dialog; export from PyPost or hand-write the documented shape |
| An entry is listed as `Entry 3: missing or empty "name" field` | That record had no usable `name`, so it could not be labelled | `name` is the one required field on a collection record |
| Result dialog is unsuccessful and lists save failures | At least one `save_collection` write failed (disk full, permissions, read-only data directory); apply reloaded memory from disk (PYPOST-1004) and recounted summary metrics (PYPOST-1058) | Read ERROR `collection_import_save_failed` for failing ids, then WARNING `collection_import_reconciled`; the tree and summary dialog both reflect the durable persisted state (failed items report 0 added/updated and list save errors) |
| Imported requests do not send correctly | `{{placeholders}}` are imported verbatim and need their environment | Select the matching environment — see [Environments Dialog](environments_dialog.md) |
| An imported collection appears as `Copy of X` without a prompt | Two entries in the same file shared that name | Expected: in-file duplicates are always renamed, since neither is a collection you already had |
| Result dialog "Renamed" count is lower than the number of `Copy of …` names in the tree | `renamed` was stored as a dict keyed by original name (fixed in PYPOST-1003) | Confirm you are on a build where `CollectionImportPlanResult.renamed` is `list[tuple[str, str]]`; n same-named duplicates should report n−1 renames |
| Agents suddenly see new MCP tools | Imported requests had `expose_as_mcp: true` and a running endpoint selected that collection; `collections_changed` refreshes only those endpoint(s) | Review that collection's MCP flags and endpoint selection before importing — see [MCP Integration](mcp_integration.md) |
| WARNING `collection_import_worker_finish_wait_timeout` | Short post-`finished` join did not complete within `_WORKER_FINISH_WAIT_MS` | Same class of issue as storage gateway finish hygiene (PYPOST-829); usually transient; escalate if paired with crashes under rapid import churn |

## Related

- [Collection Export](collection_export.md) — write a collection to the same JSON shape
  (PYPOST-989; context-menu entry point PYPOST-1013)
- [Collection Storage](collection_storage.md) — the on-disk format this feature reads
- [Collection Loading](collection_loading.md) — the async startup path that shares
  `apply_loaded_collections` and the worker finish-teardown pattern
- [Async Environment Storage](environment_storage_async.md) — sibling `QThread` + finish
  wait hygiene
- [Environments Dialog](environments_dialog.md) — the environment import precedent
- [UI Identity](ui_identity.md) — `COLLECTION_IMPORT_BUTTON` and the widget-id convention
