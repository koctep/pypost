# Collection Import

## Overview

**Import Collection** (PYPOST-987, PYPOST-1220) loads one or more collections, with all of their
requests and variable schemas, from a JSON or YAML file into the running app. The accepted format
is PyPost's own collection serialization (format v1 or format v2) — a copy of a
`{data_dir}/collections/{id}.json` file, a self-contained `.yaml`/`.yml` file, or a list
of such objects. Foreign formats (Postman, Insomnia, OpenAPI) are explicitly out of
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

**PYPOST-1063** closes remaining asynchronous collection-import test gaps, adding automated test
coverage for busy re-entry prevention, unexpected reader exceptions caught by the worker thread,
status bar lifecycle message transitions, and real-file disk JSON parsing in
`tests/test_collection_import_async_gaps.py`.

**PYPOST-1182** introduces deterministic lifecycle synchronization APIs
(`CollectionImportActions.wait_idle` and `CollectionsPresenter.wait_import_idle`) to eliminate Qt
event loop wait hangs and worker thread teardown race conditions during test suite execution
(`tests/test_collections_import_ui.py`).

**PYPOST-1148** resolves indefinite futex deadlocks during full test suite runs (2,700+ tests)
by establishing deterministic `teardown()` contracts on `CollectionImportActions` and
`CollectionsPresenter`, refining the `is_busy()` contract (`self._preparing or self._worker is
not None`) to prevent premature idle detection, safely disconnecting signals, interrupting
and joining background worker threads, and draining deferred deletion events before widget
destruction.

**PYPOST-1228** replaces that boolean `_preparing` flag plus `_worker is not None` check with a
formal `CollectionImportState` enum (`pypost/core/collection_import_state.py`: `IDLE`,
`PREPARING`, `PARSING`, `APPLYING`) and fixes a real bug the two-flag scheme had: because
`_on_parse_completed()` cleared `_preparing` *before* running `_finish_import()` (conflict
prompts → plan → apply → refresh — the applying phase), and `_worker` could already be `None`
by then if the worker's `finished` signal had already been processed, `is_busy()` could report
`False` for the entire applying window. A second `import_collections()` call arriving during
that window (e.g. from a modal conflict dialog pumping the event loop) was not reliably
rejected. `_state` now transitions to `APPLYING` synchronously before `_finish_import()` runs
and back to `IDLE` as its last statement, closing the gap. See [State machine
(PYPOST-1228)](#state-machine-pypost-1228) below.

**PYPOST-1229** adds cooperative cancellation for in-flight parsing. The worker uses
`QThread.requestInterruption()` and checks the interruption flag before parsing, at each
`on_progress` checkpoint, and after the reader returns immediately before publishing
`parse_completed`. An interrupted parse emits `parse_cancelled`; it does not emit a completion or
failure signal. The presenter returns to `IDLE`, clears its busy cue, and does not show a dialog,
refresh the tree, apply results, or emit a collections-changed event. Cancellation is cooperative
and best-effort: a reader must call `on_progress` to be interruptible during its record loop, and
file decoding or one expensive record can delay observation. No forcible thread termination is used.

**PYPOST-1230** extracts the repeated presenter-import wait used by the collection-import UI tests
into the test-only `tests/helpers/collection_import_wait.py` module. It does not add a production
dependency or change the import lifecycle; it centralizes the test condition that an expected
outcome is visible and the presenter has become idle.

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

- **`pypost/core/collection_import_state.py`** — `CollectionImportState`, a Qt-free
  `str, Enum` (`IDLE`, `PREPARING`, `PARSING`, `APPLYING`) naming what
  `CollectionImportActions` is doing right now, following the `ImportConflictDecision(str,
  Enum)` precedent in `import_conflicts.py` (PYPOST-1228). Replaces the earlier `_preparing`
  bool plus `_worker is not None` presence check.
- **`pypost/core/collection_import.py`** — the pure core. No Qt, no storage. Parses a
  file into candidate `Collection` models, detects name conflicts, reserves colliding
  ids, computes the resulting collection list, recounts plan results against save
  failures (`recount_collection_import_plan`), and formats the summary text. Directly
  unit-testable without a `QApplication` or a data directory. Called from the parse
  worker via the injected `read_import_file` callable (default
  `load_collection_import_candidates`).
- **`pypost/core/qt/collection_import_parse_worker.py`** —
  `CollectionImportParseWorker` (`QThread`). Runs `read_import_file(path)` off the GUI
  thread; emits `parse_completed(collections, parse_errors)`, `parse_failed(error)`, or
  `parse_cancelled()`. No widget access. Same one-shot worker shape as `PasteJsonFormatWorker` /
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
  a `QObject` orchestrator. Owns worker lifecycle, busy state, and teardown; sequences
  pick → async parse → sync conflict/plan/apply/result. Exposes `is_busy()`, `wait_idle()`,
  and `teardown()` for bounded lifecycle coordination, signal disconnection, and deferred
  event processing (PYPOST-1148, PYPOST-1182). Split out of `CollectionsPresenter` the same
  way `CollectionTreeActions` and `CollectionsAsyncLoader` are.
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
  for the preparing cue; keeps the optional `read_import_file` DI seam. Exposes
  `wait_import_idle()` and `teardown()` delegating to `CollectionImportActions` for clean
  worker termination and panel closure (PYPOST-1148, PYPOST-1182).

### Async parse and busy cue (PYPOST-1005)

1. User clicks **Import Collection…**; `import_collections` returns immediately if
   `is_busy()` (second click while preparing is skipped — log-and-return, not queued).
2. File picker runs on the GUI thread (unchanged).
3. Orchestrator shows the initial busy cue and starts `CollectionImportParseWorker`:
   - Status bar: `MSG_IMPORT_PREPARING` (“Preparing collection import…”), transitioning
     to `MSG_IMPORT_VALIDATING` (“Validating collections ({done}/{total})…”) as
     `parse_progress(done, total)` signals arrive from the worker.
   - Import button (`COLLECTION_IMPORT_BUTTON`) disabled via `findChild` on the panel.
4. Worker runs `read_import_file` off-thread; emits completed, failed, or cancelled.
5. If teardown requests interruption, the worker normally exits through `parse_cancelled`;
   however, the final best-effort publication race can still result in `parse_completed` if
   interruption arrives between the final check and emission. In the normal cancellation path,
   the orchestrator returns to `IDLE` without applying or displaying a result.
6. For completion or failure, the orchestrator clears the cue, then on the GUI thread either
   shows the invalid-file dialog or runs conflict prompts → `plan_collection_import` →
   `apply_imported_collections` → refresh → result dialog.
7. Worker `finished` slot: `deleteLater` + bounded `wait(100)` (PYPOST-829 hygiene;
   WARNING if the short join times out).

There is no modal `QProgressDialog` and no determinate percent bar — same class of
experience as [Collection Loading](collection_loading.md) startup async load, plus a
visible preparing cue for a user-initiated action. Plan and apply remain synchronous
after parse; only parse is off-thread.

### Cooperative cancellation (PYPOST-1229)

Cancellation is owned by the worker lifecycle, while the parser remains Qt-free:

```mermaid
sequenceDiagram
    participant UI as GUI thread
    participant W as CollectionImportParseWorker
    participant R as read_import_file
    UI->>W: start()
    W->>W: Check interruption before reader
    W->>R: read_import_file(path, on_progress)
    R-->>W: on_progress(done, total)
    W->>W: Emit parse_progress; check interruption
    UI->>W: requestInterruption() during teardown
    W-->>UI: parse_cancelled()
    UI->>UI: Set IDLE; clear cue; discard parse result
```

The production reader, `load_collection_import_candidates`, invokes `on_progress(done, total)`
once per record. The worker's callback first emits `parse_progress` and then checks
`isInterruptionRequested()`. If the flag is set, an internal `CollectionImportCancelled`
exception unwinds the reader call into `run()`, which catches it and emits exactly one
`parse_cancelled()` signal. A final check after the reader returns narrows, but does not
eliminate, the publication race: if interruption is observed after the last progress callback,
it prevents `parse_completed`, but interruption can still arrive between this check and
`parse_completed.emit()`.

`CollectionImportActions.teardown()` requests interruption before entering `wait_idle()`. The
wait pumps the Qt event loop when one exists so the cancellation signal and worker completion can
be delivered; any remaining running worker receives a final guarded request and a bounded 100 ms
join. After that bounded join attempt, the worker reference is cleared and the action state is
forced to `IDLE`, even if the join times out. This is a cooperative stop, not a kill: a reader
blocked in I/O or decoding may still be running after the wait and cause teardown to return
`False` with a timeout warning.

### State machine (PYPOST-1228)

`CollectionImportActions._state: CollectionImportState` is the single source `is_busy()`
reads. Transitions all happen synchronously on the GUI thread:

```text
        import_collections()                 worker.start()
IDLE ───────────────────────▶ PREPARING ───────────────────────▶ PARSING
  ▲                                                                  │
  │                                                     parse_completed (no valid collections)
  │                                                     or parse_failed / parse_cancelled
  │◀─────────────────────────────────────────────────────────────────┤
  │                                                                  │
  │                                          parse_completed (valid collections)
  │                                                                  ▼
  │                                                              APPLYING
  │                                                     (_finish_import: conflicts →
  │                                                      plan → apply → refresh/restore/emit)
  │                                                                  │
  └──────────────────────── end of _finish_import() ─────────────────┘

Any state ──── teardown() ────▶ IDLE
  (forced after bounded cleanup; final join may time out before the reference is cleared)
```

| From | Event / call site | To |
| --- | --- | --- |
| IDLE | `import_collections()` picks a file (not busy) → `_start_parse()` begins | PREPARING |
| PREPARING | `worker.start()` returns | PARSING |
| PARSING | `parse_completed` fires, `collections` empty | IDLE |
| PARSING | `parse_completed` fires, `collections` non-empty | APPLYING |
| PARSING | `parse_failed` fires | IDLE |
| PARSING | `parse_cancelled` fires | IDLE |
| APPLYING | `_finish_import()` reaches its final statement (after the result dialog) | IDLE |
| any | `teardown()` called | IDLE |

The bug this closes: the previous two-flag scheme (`_preparing` bool + `_worker is not None`)
cleared `_preparing` as the first statement of `_on_parse_completed()`, before `_finish_import()`
ran. `_worker` could already be `None` at that point too, if the worker's `finished` signal
(queued asynchronously, with no ordering guarantee relative to `parse_completed`) had already been
processed. When both were false, `is_busy()` reported `False` for the entire applying window —
conflict dialogs, `plan_collection_import`, `apply_imported_collections`, tree refresh — even
though an import was still actively in flight. A second `import_collections()` call arriving
during that window (a modal conflict dialog pumps the Qt event loop, so a re-entrant trigger is
possible) was not reliably rejected.

`_state` transitions to `APPLYING` synchronously inside `_on_parse_completed()`, strictly before
`_finish_import()` is invoked, and back to `IDLE` synchronously as the last statement inside
`_finish_import()`. Both edges are on the same call stack as the work they bracket, so neither
depends on the worker's `finished` signal timing — the race is removed rather than narrowed.
`self._worker` continues to be written in the same three places (`_start_parse`,
`_on_worker_finished`, `teardown`) for `QThread` lifecycle mechanics only; it is no longer
consulted by `is_busy()`.

There is no `FAILED` state: a parse failure or "no valid collections" result returns straight to
`IDLE` after the error dialog, matching pre-PYPOST-1228 behavior.

Cancellation also returns to `IDLE`, but it intentionally bypasses the error and result-dialog
paths. It applies only while parsing is in flight; once `parse_completed` has been delivered and
the presenter has entered `APPLYING`, teardown does not roll back application work.

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

### `load_collection_import_candidates(path, on_progress=None) -> (list[Collection], list[str])`

Reads and parses an import file. A single JSON object is normalized to a one-item list.

- **path**: `Path` to the file to read.
- **on_progress**: Optional callback invoked as `on_progress(done, total)` once per record.
  The worker uses this callback as its cooperative cancellation checkpoint.
- **Returns**: candidate collections, and one formatted message per rejected record.
- **Raises**: `CollectionImportFileError` for file-level problems only.

### `find_collection_conflicts(existing, incoming) -> list[str]`

Names present in both lists, in incoming order, without duplicates. Drives how many times
the conflict prompt is shown.

### `plan_collection_import(existing, incoming, decisions) -> CollectionImportPlanResult`

Applies `decisions` (`{name: ImportConflictDecision}`) and returns the plan. Pure: neither
input list is mutated. A name absent from `decisions` defaults to `SKIP`.

`CollectionImportPlanResult` carries `collections` (the complete target list), `persisted`
(the subset to write), `added` / `updated` / `skipped` / `renamed`, `request_count`,
`websocket_count`, and `parse_errors`.

`renamed` is `list[tuple[str, str]]` — one `(original_name, new_name)` pair per rename
event (Keep Both or in-file duplicate), in plan order. It is intentionally not a
`dict[str, str]`: several incoming records can share the same original name, and a dict
keyed by that name would keep only the last pair (PYPOST-1003). Downstream UI only uses
`len(result.renamed)` and truthiness; formatters iterate the pairs directly.

### `format_collection_import_result(result) -> str`

Human-readable summary for the result dialog: collection, request, and WebSocket counts
(`len(result.renamed)` for the Renamed line), every `"original" -> "new_name"` pair from
`result.renamed`, and any per-entry failures.

### `recount_collection_import_plan(plan, failed_ids) -> CollectionImportPlanResult`

Pure function adjusting import plan metrics when save failures occur (PYPOST-1058):

- **plan**: The original `CollectionImportPlanResult` computed by `plan_collection_import`.
- **failed_ids**: `set[str]` of collection IDs that failed during `save_collection`.
- **Returns**: A new `CollectionImportPlanResult` where failed collections are removed from
  `added`, `updated`, and `renamed` (both count and `(orig, new_name)` detail pairs), and
  `request_count` and `websocket_count` sum only the requests and WebSockets of successfully
  persisted collections. `skipped` and `parse_errors` are preserved.
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
- `parse_cancelled` — no payload; the worker observed a requested interruption before
  completion could be published

Workers are one-shot. On `finished`, `CollectionImportActions` schedules `deleteLater`
and a short `wait(100)` before dropping the reference (same PYPOST-829 pattern as
[Collection Loading](collection_loading.md) / [Async Environment Storage](environment_storage_async.md)).
`parse_cancelled` is mutually exclusive with `parse_completed` and `parse_failed` for one
worker run. It is emitted only for cooperative interruption observed by the worker; it is not
an error signal.

### `CollectionImportActions`

`QObject` owned by the presenter. Public surface:

- **`is_busy() -> bool`** — returns `True` whenever `self._state is not
  CollectionImportState.IDLE`, i.e. while preparing, parsing, or applying (PYPOST-1228). A second
  Import click while busy is ignored (`collection_import_skipped reason=busy`). Prior to
  PYPOST-1228 this was `self._preparing or self._worker is not None` (refined in PYPOST-1148 to
  check `self._worker is not None` rather than `self._worker.isRunning()`, to prevent premature
  idle detection while worker finalization (`_on_worker_finished`), signal delivery, or teardown
  was in flight); that two-flag scheme could still report `False` during the applying phase — see
  [State machine (PYPOST-1228)](#state-machine-pypost-1228). `self._worker` remains, but purely
  for `QThread` lifecycle mechanics (`wait_idle()`'s no-`QApplication` fallback, `teardown()`'s
  disconnect/interrupt/cleanup sequence); it no longer feeds `is_busy()`.
- **`wait_idle(timeout_ms: int = 5000) -> bool`** — while the action is busy, pumps the Qt
  event loop (`QApplication.processEvents()`) or performs short worker waits when no
  `QApplication` exists until `is_busy()` becomes `False`. The event-loop passes allow queued
  parse, result, and worker-cleanup handlers to run, but this method does not explicitly call
  `QThread.wait()` on the `QApplication` path or guarantee that `finished` has been processed
  and the worker reaped when it returns. It performs one additional event-loop pass after idle
  to allow deferred deletion (`deleteLater()`) to run. Returns `True` if idle is observed within
  `timeout_ms`, or `False` if the bounded wait expires (PYPOST-1182, PYPOST-1148).
- **`teardown(timeout_ms: int = 5000) -> bool`** — coordinates interruption, signal
  disconnection, bounded waiting, and worker cleanup (PYPOST-1148):
  1. If the worker is running, requests interruption before waiting so an in-flight parse can
     reach its next checkpoint.
  2. If `is_busy()`, calls `wait_idle(timeout_ms)` to process events while cancellation or
     completion settles. `wait_idle()` does not synchronously join or reap on the
     `QApplication` path.
  3. Safely disconnects all worker Qt signals (`parse_progress`, `parse_completed`,
     `parse_failed`, `parse_cancelled`, `finished`) within guarded `try...except
     (RuntimeError, TypeError)` blocks, preventing callbacks from firing on a dying presenter.
  4. If the worker remains active, requests interruption again and waits boundedly (100ms) for
     thread exit. This final join can time out.
  5. After that bounded join attempt, schedules `worker.deleteLater()`, clears
     `self._worker = None`, and resets the state to `IDLE`, even if the join timed out.
  6. Flushes pending Qt events via `app.processEvents()` to process deferred deletions.
  Returns `True` if no bounded wait timed out, or `False` if the idle wait or final join timed
  out. A `False` result does not prevent the reference/state cleanup in steps 5–6.
- **`import_collections() -> None`** — pick file; dispatch async parse; finish on the
  GUI thread when ready. Callers and the button wire-up do not change.

Constructor DI (beyond the original refresh/emit hooks): optional `show_status` /
`clear_status` for the preparing message; `read_import_file` for the worker.

When supplying `read_import_file`, prefer the supported callback shape:

```python
def read_import_file(
    path: Path,
    on_progress: Callable[[int, int], None] | None = None,
) -> tuple[list[Collection], list[str]]:
    ...
```

Call `on_progress(done, total)` once per record and let exceptions from that callback propagate.
The worker uses that callback as its per-record cancellation checkpoint. A legacy one-argument
reader remains supported, but can only observe interruption before it starts or after it returns;
it cannot be stopped during its internal work.

### `CollectionsPresenter.wait_import_idle(timeout_ms: int = 5000) -> bool`

Delegates directly to `CollectionImportActions.wait_idle(timeout_ms)`. Allows UI harnesses, parent
presenters, and automated test fixtures to wait, within a bound, for the import action to report
`IDLE` while giving queued Qt lifecycle handlers an opportunity to run. It does not itself
guarantee that the native worker has been joined and reaped; call `teardown()` before destroying
widgets or closing panels (PYPOST-1182).

### `CollectionsPresenter.teardown(timeout_ms: int = 5000) -> bool`

Deterministically tears down import actions and presenter resources (PYPOST-1148). Delegates to
`self._import_actions.teardown(timeout_ms=timeout_ms)` and closes the presenter panel
(`self._panel.close()`). Returns `True` if background worker resources were cleanly drained and
stopped. Test fixtures and parent widget cleanup routines invoke `teardown()` in `finally:` blocks
to prevent background thread leaks and C++ destructor futex deadlocks during test suite runs.

Presenter integrations should call `wait_import_idle()` before making assertions that depend on
parse completion, and call `teardown()` before closing the panel or destroying its parent. Do not
replace this lifecycle with `QThread.terminate()` or direct result application: the action owns
signal disconnection, cooperative interruption, bounded joining, and the cancellation terminal
state.

### Testing seam

`CollectionsPresenter.__init__` accepts an optional `read_import_file` callable,
defaulting to `load_collection_import_candidates`. Qt tests inject a stub reader to
exercise the flow without touching disk; the end-to-end test omits it and drives the real
parser, `RequestManager`, and `StorageManager` against a `tmp_path`.

Because parse is async, UI tests must wait for completion rather than asserting immediately after
`import_collections()`. Use the shared `wait_import()` helper below for the normal outcome-plus-idle
contract. Stubs used from the worker thread must be thread-safe.

### Shared import wait helper for presenter tests (PYPOST-1230)

`tests/helpers/collection_import_wait.py` provides the test-only `wait_import()` helper. It
combines a scenario-owned outcome predicate with the presenter's import lifecycle state and
delegates event-loop processing and deadline enforcement to
`tests.helpers.process_until.process_until`.

#### API

```python
def wait_import(
    done: Callable[[], bool],
    presenter: _ImportPresenter | None = None,
    timeout_ms: int = 5_000,
) -> None:
    ...
```

- `done` is a zero-argument predicate supplied by the test. It should be a repeatable,
  side-effect-free observation such as `lambda: mock_result.call_count >= 1`.
- `presenter` is optional. When supplied, it must expose the test-visible
  `presenter._import_actions.is_busy()` surface. The helper waits for that value to become
  `False` after the outcome predicate becomes true.
- `timeout_ms` is the wall-clock bound passed to `process_until()`. It defaults to 5,000 ms and
  can be overridden for a deliberately slower test.
- The helper returns `None` only after the required condition is complete. If the condition is not
  reached, it raises `AssertionError` with the configured bound and lazy diagnostic state:
  `outcome=<last observed value>` and, when a presenter is supplied, `busy=<current value>`.

The combined predicate is evaluated in this order on each event-loop turn: `done()` must first be
true, then the optional presenter's `_import_actions.is_busy()` must be false. An outcome callback
can therefore become visible before queued apply, refresh, signal, or return-to-idle work has
finished without releasing the test wait. With no presenter, the helper waits only for `done()`.
`process_until()` pumps a nested Qt event loop with its bounded polling and watchdog behavior; the
helper does not create a second timeout mechanism.

The helper only observes lifecycle state. It does not call `wait_import_idle()`, interrupt a worker,
join a thread, close a panel, or perform teardown. Tests still own resource cleanup and should call
`presenter.teardown()` in fixture cleanup when the presenter can have an active worker. A timeout
does not imply that the worker was stopped.

#### Migrating a presenter UI test

Import the shared helper, remove the local `_wait_import()` implementation, and preserve each
test's existing outcome predicate and presenter argument:

```python
from tests.helpers.collection_import_wait import wait_import

try:
    presenter.import_collections()
    wait_import(lambda: mock_result.call_count >= 1, presenter)
    assert mock_result.call_args.kwargs["success"] is True
finally:
    presenter.teardown()
```

Use `presenter=None` only when the test has no presenter lifecycle to observe. Do not migrate
specialized waits whose contract is different, such as cancellation checkpoints, progress
signals, responsiveness timers, or explicit teardown tests. Those tests should keep their
purpose-specific predicates and cleanup sequencing.

#### Contributor validation

Run repository checks through Make targets. The focused collection-import helper and UI tests can
be run together with:

```sh
make test \
  PYTEST_ARGS='tests/test_collection_import_wait_repro.py tests/test_collections_import_ui.py'
```

For the surrounding repository gates, use:

```sh
make lint
make typecheck
make verify-ai-tasks
make check
```

`make check` runs the combined lint, fast-test, and AI-task-artifact checks. If it reports an
unrelated baseline failure, compare the failing test node with the existing baseline Jira issues
before attributing it to the import test helper. Do not replace these commands with direct test,
linter, type-checker, or artifact-verification invocations.

### Worker thread lifecycle synchronization and test unhanging (PYPOST-1182)

Background worker threads started by UI presenters need explicit lifecycle synchronization before
callers and test harnesses destroy enclosing widgets or move to the next test. `wait_idle()`
provides a bounded wait for the action to report `IDLE`; `teardown()` handles interruption,
signal disconnection, and the final bounded worker wait.

Without deterministic synchronization:
1. When `CollectionImportParseWorker` emits `parse_completed`, Qt delivers the signal to the GUI thread
   via a queued connection.
2. `CollectionImportActions._finish_import()` executes synchronously on the GUI thread, triggering tree
   refreshes and showing the result dialog.
3. If test helpers exit immediately upon observing dialog invocation (e.g. `mock_result.called`), the
   test function returns, calling `presenter.panel.close()` and deallocating Qt objects while the
   background `QThread` native thread is still completing its OS run loop or emitting queued `finished`
   signals.
4. This causes `pthread_join` deadlocks, memory races, or event loop starvation across subsequent tests
   in `make test`.

Use the lifecycle synchronization as follows:
- **`CollectionImportActions.wait_idle(timeout_ms=5000)`** pumps the `QApplication` event loop
  in a bounded loop until `is_busy()` returns `False`. It may deliver queued worker-finish and
  deferred-cleanup handlers, but it is not an explicit native-thread join on the
  `QApplication` path.
- **`CollectionsPresenter.wait_import_idle(timeout_ms=5000)`** exposes this wait condition on the
  presenter.
- In `tests/test_collections_import_ui.py`, shared test helper `wait_import(done, presenter)` waits
  until `done()` is `True` and, when a presenter is supplied, checks
  `presenter._import_actions.is_busy()` directly. It does not call
  `presenter.wait_import_idle()` or perform teardown. These tests own their cleanup and should
  use `presenter.teardown()` when a worker may still be active.
- Automated tests in headless mode (`QT_QPA_PLATFORM=offscreen`) also patch dialog handlers in
  `collection_item_dialogs.py` to ensure unexpected branches fail fast with descriptive assertions
  rather than opening blocking modal dialog loops (`QDialog.exec()`).

### Futex deadlock elimination during full test suite execution (PYPOST-1148)

Running the complete fast test suite in batch mode (`make test` or `make check`) uses the test
runner to execute each test file in an isolated subprocess, with a separate `QApplication` per
process as needed. It does not execute all tests in one Python process with a shared
`QApplication`. The collection import error tests historically exposed an unrecoverable futex
deadlock (`futex_wait_queue`) around worker cleanup
(`tests/test_collection_import_async_gaps.py`).

#### Root cause analysis

1. **Premature test completion on reader exception**:
   When reader fixtures raised unexpected exceptions (such as `_exploding_reader`),
   `CollectionImportParseWorker` caught the error and emitted `parse_failed(error)`.
   On the main thread, `_on_parse_failed()` immediately invoked
   `show_collection_import_invalid_file_error()`. Tests monitoring the mock dialog observed
   `mock_invalid.called` and returned without waiting for the background `QThread` to finish.
2. **Premature `is_busy()` false negative**:
   Previously, `is_busy()` returned `self._preparing or (self._worker and`
   `self._worker.isRunning())`. When `_on_parse_failed()` ran, it set `self._preparing = False`.
   As soon as the worker exited its Python `run()` method, `isRunning()` evaluated to `False`.
   However, the queued `finished` signal had not yet been processed by the GUI event loop,
   leaving `_on_worker_finished()` uncalled, native thread join unperformed, and `_worker`
   still holding an active native thread reference.
3. **GIL contention and C++ destructor futex deadlock**:
   Upon test completion, `presenter` fell out of scope. In a full run of 2,700+ tests, Python
   garbage collection cycles deallocated the Python `CollectionImportParseWorker` wrapper.
   Its underlying Qt C++ destructor `QThread::~QThread()` detected an active or terminating
   OS thread and invoked `pthread_join()`, sleeping on a Linux futex while holding the
   Python GIL. Concurrently, the exiting native worker thread required the Python GIL or
   Qt event dispatcher mutexes to complete thread termination. Because the main GUI thread
   held the GIL during GC while blocked in `pthread_join()`, a circular deadlock occurred.
   Signal-based timeouts (`SIGALRM` via `pytest-timeout`) could not interrupt glibc pthreads
   kernel futex waits, causing pytest to hang indefinitely.

#### Architectural resolution

- **Refined `is_busy()` lifecycle contract**:
  `CollectionImportActions.is_busy()` now reads the `CollectionImportState` enum. An import action
  remains busy through preparing, parsing, and applying, and returns idle only through an explicit
  terminal state transition.
- **Explicit `teardown()` cleanup protocol**:
  `CollectionImportActions.teardown(timeout_ms)` and `CollectionsPresenter.teardown(timeout_ms)`
  provide bounded lifecycle cleanup:
  - **Interrupt**: Requests `worker.requestInterruption()` before waiting so a running reader can
    unwind at its next checkpoint (PYPOST-1229).
  - **Wait**: Invokes `wait_idle(timeout_ms)` to process events while active workers cancel or
    finish until `is_busy()` reports `False`. It does not explicitly join or reap on the
    `QApplication` path.
  - **Disconnect**: Safely disconnects all Qt signals (`parse_progress`, `parse_completed`,
    `parse_failed`, `parse_cancelled`, `finished`) within `try...except (RuntimeError, TypeError)`
    blocks.
  - **Join**: If the worker thread remains running, requests interruption again and waits boundedly
    (100ms) for clean exit. This final join can time out.
  - **Cleanup & Defer Delete**: After the bounded join attempt, invokes `worker.deleteLater()`,
    clears `self._worker = None`, resets state to `IDLE`, and pumps `app.processEvents()` to
    process deferred deletion events before widget teardown. Clearing the reference and forcing
    `IDLE` do not prove that a timed-out native worker has joined.
- **Harness synchronization**:
  All asynchronous collection import tests in `tests/test_collection_import_async_gaps.py`
  synchronize via `presenter.wait_import_idle()` before assertions and invoke
  `presenter.teardown()` in `finally:` blocks. Teardown is bounded cleanup and can report a
  timeout; these calls do not guarantee zero thread leaks in every failure mode.

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
  `reason=no_valid_collections`. Same `wait_import()` as the dialog.
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

There is no new application setting, environment variable, on-disk format,
`StorageInterface` method, or third-party dependency. The file-dialog filter, caption, and
preparing status text are constants in `collection_messages.py`.

The lifecycle methods expose bounded waits for callers that need a different test or teardown
budget:

- `CollectionImportActions.wait_idle(timeout_ms=5000)` pumps the Qt event loop while waiting for
  the action to report `IDLE`; queued cleanup may clear the worker reference, but this method does
  not explicitly join the worker on the `QApplication` path.
- `CollectionImportActions.teardown(timeout_ms=5000)` requests interruption before waiting. If a
  worker is still running after that wait, teardown performs one additional fixed 100 ms join
  (`_WORKER_FINISH_WAIT_MS` is also 100 ms for the normal `finished` path).

These are lifecycle bounds, not a guarantee that parsing itself can be preempted. A custom reader
that blocks in I/O, decoding, or one expensive record can cause `wait_idle()` or `teardown()` to
return `False` and log a timeout. No forcible termination fallback exists.

## Observability

Structured `key=value` lines. Names, URLs, headers, bodies, scripts, full candidate
lists, and the status-bar string itself are never logged — an imported collection
routinely carries credentials in a header template. Paths are logged for triage
(user-chosen import file). See `ai-tasks/PYPOST-987/50-observability.md`,
`ai-tasks/PYPOST-1004/50-observability.md`,
`ai-tasks/PYPOST-1005/50-observability.md`,
`ai-tasks/PYPOST-1006/50-observability.md`,
`ai-tasks/PYPOST-1058/50-observability.md`,
`ai-tasks/PYPOST-1059/50-observability.md`,
`ai-tasks/PYPOST-1182/50-observability.md`, and
`ai-tasks/PYPOST-1148/50-observability.md`.

### Async parse, lifecycle synchronization, and teardown (PYPOST-1005 / PYPOST-1182 / PYPOST-1148 /
PYPOST-1229)

In `collections_presenter.py`:

- **INFO** `collections_presenter_teardown_started timeout_ms=%d` — start of presenter-level
  teardown sequence (PYPOST-1148)
- **INFO** `collections_presenter_teardown_completed clean=%s` — completion of presenter
  teardown (PYPOST-1148)

In `collection_import_actions.py`:

- **DEBUG** `collection_import_state_changed from=%s to=%s` — every `CollectionImportState`
  transition (`_set_state`), e.g. `from=parsing to=applying` (PYPOST-1228)
- **INFO** `collection_import_skipped reason=busy` — second Import while preparing
- **INFO** `collection_import_parse_started path=…` — orchestrator dispatched the worker
- **DEBUG** `collection_import_busy_cue_shown` / `collection_import_busy_cue_cleared`
- **INFO** `collection_import_wait_idle_started` — entered `wait_idle()` while worker active
  (PYPOST-1182)
- **INFO** `collection_import_wait_idle_completed elapsed_ms=%d` — `wait_idle()` observed the
  action become idle within the timeout; this is not an explicit native-thread join
  (PYPOST-1182)
- **WARNING** `collection_import_wait_idle_timeout elapsed_ms=%d` — `wait_idle()` reached
  its timeout before the action became idle (PYPOST-1182)
- **INFO** `collection_import_teardown_started timeout_ms=%d` — start of actions teardown
  (PYPOST-1148)
- **INFO** `collection_import_teardown_completed clean=%s` — completion of actions teardown
  (PYPOST-1148)
- **WARNING** `collection_import_worker_interrupting` — worker active when teardown started;
  interruption requested (PYPOST-1148)
- **WARNING** `collection_import_worker_interrupt_timeout` — worker interruption wait (100ms)
  timed out (PYPOST-1148)
- **INFO** `collection_import_worker_interrupted` — running worker stopped successfully after
  interruption (PYPOST-1148)
- **INFO** `collection_import_parse_cancelled from_state=…` — the GUI received the dedicated
  cancellation signal and returned the presenter to `IDLE` without applying results (PYPOST-1229)
- **DEBUG** `collection_import_worker_reaped` — worker reference reaped and scheduled for
  deletion (PYPOST-1148)
- **ERROR** `collection_import_parse_unexpected error=…` — unexpected exception from the
  worker, handled on the GUI thread (invalid-file dialog)
- **WARNING** `collection_import_worker_finish_wait_timeout wait_ms=…` — short join after
  `QThread.finished` did not complete

In `collection_import_parse_worker.py`:

- **DEBUG** `collection_import_parse_worker_started path=…`
- **DEBUG** `collection_import_parse_worker_completed path=… count=… error_count=…`
- **INFO** `collection_import_parse_worker_cancelled path=…` — the worker observed interruption
  and unwound without publishing parse results (PYPOST-1229)
- **WARNING** `collection_import_parse_worker_failed path=… reason=…` —
  `CollectionImportFileError`
- **ERROR** `collection_import_parse_worker_failed path=… error=…` — unexpected exception
  (`exc_info=True`)

Happy-path operator order (INFO/default): `collection_import_parse_started` → (core
`collection_import_file_parsed` when using the real loader) → apply lines →
`collection_import_completed`. Enable DEBUG to confirm busy-cue show/clear and worker
start/complete around that span.

Cancellation order is normally `collection_import_worker_interrupting` →
`collection_import_parse_worker_cancelled` → `collection_import_parse_cancelled from_state=parsing`
→ `collection_import_teardown_completed clean=True`. The exact order of worker-finish and teardown
lines can vary with Qt event delivery; the cancellation and completion signals remain mutually
exclusive.

Malformed, unreadable, or wrong-shaped file failures (`CollectionImportFileError`) are logged
twice on purpose: worker WARNING confirms the off-thread failure, and the orchestrator then
emits the terminal `collection_import_file_invalid` “nothing changed” event used since
PYPOST-987. A parse that returns no valid collections also emits that event with
`reason=no_valid_collections`.

Unexpected reader exceptions follow a different path: the worker logs
`collection_import_parse_worker_failed` at ERROR level, and the orchestrator logs
`collection_import_parse_unexpected` at ERROR level before showing the invalid-file dialog.
They do not emit `collection_import_file_invalid`.

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

- **Window freezes while importing a large file**
  - Cause: Pre-PYPOST-1005 synchronous parsing on the GUI thread, or a pathological
    plan/apply hitch after a fast parse.
  - Fix: Confirm the build uses `CollectionImportParseWorker`. During preparation, the
    status bar should show “Preparing collection import…” and Import should remain disabled
    while the window remains interactive.

- **Second Import click does nothing while preparing**
  - Cause: The busy re-entry guard (`is_busy`) ignores the click instead of queuing it.
  - Fix: Wait for the preparing cue to clear, then click again. Look for INFO
    `collection_import_skipped reason=busy`.

- **"No valid collections found in this file."**
  - Cause: The file parsed, but every entry was rejected. A foreign format whose root
    object has no top-level `name` is a common cause.
  - Fix: Check the per-entry reasons below the message in the same dialog. Export from
    PyPost or hand-write the documented shape.

- **An entry is listed as `Entry 3: missing or empty "name" field`**
  - Cause: The record had no usable `name`, so it could not be labelled.
  - Fix: `name` is the one required field on a collection record.

- **Result dialog is unsuccessful and lists save failures**
  - Cause: At least one `save_collection` write failed due to disk space, permissions,
    or a read-only data directory. Apply reloaded memory from disk (PYPOST-1004) and
    recounted summary metrics (PYPOST-1058).
  - Fix: Read ERROR `collection_import_save_failed` for failing ids, then WARNING
    `collection_import_reconciled`. The tree and summary dialog reflect the durable
    state; failed items report 0 added/updated and list save errors.

- **Imported requests do not send correctly**
  - Cause: `{{placeholders}}` are imported verbatim and need their environment.
  - Fix: Select the matching environment — see [Environments Dialog](environments_dialog.md).

- **An imported collection appears as `Copy of X` without a prompt**
  - Cause: Two entries in the same file shared that name.
  - Fix: This is expected. In-file duplicates are always renamed because neither is a
    collection that already existed.

- **Result dialog "Renamed" count is lower than the number of `Copy of …` names**
  - Cause: `renamed` was stored as a dict keyed by original name (fixed in PYPOST-1003).
  - Fix: Confirm `CollectionImportPlanResult.renamed` is
    `list[tuple[str, str]]`; n same-named duplicates should report n−1 renames.

- **Agents suddenly see new MCP tools**
  - Cause: Imported requests had `expose_as_mcp: true` and a running endpoint selected
    that collection; `collections_changed` refreshes only those endpoint(s).
  - Fix: Review the collection's MCP flags and endpoint selection before importing — see
    [MCP Integration](mcp_integration.md).

- **WARNING `collection_import_worker_finish_wait_timeout`**
  - Cause: The short post-`finished` join did not complete within
    `_WORKER_FINISH_WAIT_MS`.
  - Fix: This is the same class of issue as storage gateway finish hygiene (PYPOST-829).
    It is usually transient; escalate if paired with crashes under rapid import churn.

- **WARNING `collection_import_wait_idle_timeout`**
  - Cause: `wait_idle()` reached its timeout before the import action reported `IDLE`.
    A slow reader or queued worker cleanup may be responsible.
  - Fix: Check whether `read_import_file` is blocked on slow I/O or a deadlocked event
    loop. Use `teardown()` when interruption and a bounded final worker wait are needed;
    increase `timeout_ms` for legitimate massive-file parses.

- **Test suite stalls or hangs on `test_collections_import_ui.py`**
  - Cause: Widget teardown or garbage collection occurred while
    `CollectionImportParseWorker` was still running.
  - Fix: Use `presenter.wait_import_idle()` before assertions, then call
    `presenter.teardown()` before closing the panel or exiting test fixtures.

- **Futex deadlock in batch tests (2,700+ tests)**
  - Cause: An active worker `QThread` was deallocated during garbage collection while
    its C++ destructor waited in `pthread_join`.
  - Fix: Call `presenter.teardown()` in a `finally` block and use
    `wait_import_idle()` before assertions (PYPOST-1148).

- **Panel close does not cancel promptly**
  - Cause: The reader is decoding a large file, processing one expensive record, or does
    not invoke `on_progress`.
  - Fix: Treat cancellation as cooperative. Use the supported reader callback shape and
    keep per-record work bounded. Large-file decoding and single-record latency are
    tracked by [PYPOST-1267](https://pypost.atlassian.net/browse/PYPOST-1267).

- **`parse_completed` appears after cancellation was requested**
  - Cause: `parse_completed` may already have been published before interruption was requested,
    or interruption can arrive in the small residual window after the final guard and before
    `parse_completed.emit()`. A legacy reader without `on_progress` delays interruption
    observation while its own work is running, but the final guard still applies when the reader
    returns. The residual publication race is the only path that can publish after the final
    check.
  - Fix: Check the worker and presenter cancellation logs. The final post-reader guard narrows
    but does not eliminate the publication race; interruption can still arrive between that
    check and `parse_completed.emit()`. A legacy reader may be uninterruptible during its own
    work, and cancellation does not roll back work already in `APPLYING`.

- **WARNING `collection_import_worker_interrupt_timeout`**
  - Cause: The worker failed to stop within the bounded 100 ms interruption join.
  - Fix: Check whether the custom reader is blocked in uninterruptible I/O or decoding,
    or in a long single-record operation. No forcible termination fallback exists
    (PYPOST-1229).

### Known follow-ups

The cooperative cancellation and lifecycle behavior have these linked follow-ups, as recorded
in [PYPOST-1229 technical debt](../../ai-tasks/PYPOST-1229/60-tech-debt.md):

- **[PYPOST-1264](https://pypost.atlassian.net/browse/PYPOST-1264)** — consolidate teardown
  interruption and join policy, including review of the inherited 5000 ms and 100 ms budgets.
- **[PYPOST-1265](https://pypost.atlassian.net/browse/PYPOST-1265)** — expand cancellation
  coverage with real JSON/YAML input, pre-start interruption, exact signal counts, and the
  legacy-reader contract.
- **[PYPOST-1266](https://pypost.atlassian.net/browse/PYPOST-1266)** — define a typed
  cancellation-aware `ReadImportFile` protocol, remove the dynamic reader fallback, and add
  contract tests for supported reader shapes.
- **[PYPOST-1267](https://pypost.atlassian.net/browse/PYPOST-1267)** — make large-file
  loading/decoding cancellation-aware through streaming or bounded decode checkpoints, with
  a cancellation-latency test.
- **[PYPOST-1261](https://pypost.atlassian.net/browse/PYPOST-1261)** — pre-existing malformed
  nested-expression, frozen SOLID snapshot, and process-level Qt baseline failures.
- **[PYPOST-1262](https://pypost.atlassian.net/browse/PYPOST-1262)** — pre-existing,
  load-sensitive nested-Make timeout failures.

### Pre-existing baseline failures

The full `make test` run can also report failures unrelated to collection-import cancellation.
Use the focused cancellation and adjacent import tests to isolate this feature, then compare a
full run with the task-base evidence in [PYPOST-1229 technical debt](../../ai-tasks/PYPOST-1229/60-tech-debt.md).

- **PYPOST-1261** tracks malformed nested-expression expectations and the frozen SOLID snapshot,
  plus process-level Qt failures observed in full runs. The tracked test nodes are in
  `tests/test_function_expression_resolver.py`, `tests/test_solid_audit_baseline.py`, and
  `tests/test_template_service.py`; the Qt process nodes are
  `tests/test_env_dialog.py::<module>` and `tests/test_environment_list_widget.py::<module>`.
- **PYPOST-1262** tracks load-sensitive nested-Make timeouts in
  `tests/test_makefile_lifecycle.py::TestVenvExtraStampIdempotency::test_venv_test_installs_when_stamp_stale`
  and `tests/test_makefile_targets.py::TestTargetExecution::test_test_succeeds_from_bare_venv_via_venv_test`.

These baseline issues do not explain a cancellation regression. A cancellation-specific failure
is indicated by a missing `parse_cancelled` signal, an unexpected `parse_completed`/`parse_failed`
signal, result application after an in-flight interruption, or a new failure in the focused import
tests.

## Related

 - [Collection Export](collection_export.md) — write a collection to the same JSON shape
   (PYPOST-989; context-menu entry point PYPOST-1013)
 - [Collection Format v2](collection_format_v2.md) — self-contained collection format v2 with YAML and JSON serialization
 - [Collection Storage](collection_storage.md) — the on-disk format this feature reads
 - [Collection Loading](collection_loading.md) — the async startup path that shares
   `apply_loaded_collections` and the worker finish-teardown pattern
 - [Async Environment Storage](environment_storage_async.md) — sibling `QThread` + finish
   wait hygiene
 - [Environments Dialog](environments_dialog.md) — the environment import precedent
 - [UI Identity](ui_identity.md) — `COLLECTION_IMPORT_BUTTON` and the widget-id convention
