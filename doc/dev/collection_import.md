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
  ids, computes the resulting collection list, and formats the summary text. Directly
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
  SOLID audit cap (`scripts/audit_baseline_metrics.py`).
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
3. Orchestrator shows the busy cue and starts `CollectionImportParseWorker`:
   - Status bar: `MSG_IMPORT_PREPARING` (“Preparing collection import…”) via injected
     `show_status` / `clear_status` callables.
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

### `apply_imported_collections(manager, collections, persisted) -> list[str]`

Swaps in the planned list via `RequestManager.apply_loaded_collections` (which rebuilds
`_request_index`) and writes each collection in `persisted`. Returns one formatted message
per collection that could not be written; the loop continues past a failure so one bad
write cannot strand the rest.

If any write raises `OSError`, the function calls `manager.reload_collections()` before
returning so in-memory collections and `_request_index` match durable storage
(PYPOST-1004). Successful sibling writes stay on disk and remain visible after reload;
failed ones are absent or revert to the previous on-disk file. When every write succeeds,
there is no reload.

Deliberately **not** routed through `RequestManager.create_collection`, which rejects
duplicate names: an import resolves name conflicts through an explicit user decision and
may legitimately produce a name `create_collection` would refuse.

### Result dialog after save failure (contract B)

After apply returns with save failures (and memory has been reconciled),
`CollectionImportActions` still formats the result from the **plan** (`added` /
`updated` / `skipped` / `renamed` / `request_count`), appends the save-failure lines,
sets `success=False`, refreshes the tree (now durable-aligned), and shows the
unsuccessful dialog. Plan counts describe the attempted import; they are **not**
recomputed against the post-reload durable set. The tree shows what is on disk; the
dialog shows what was attempted plus which saves failed.

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

## Configuration

None. No new setting, environment variable, on-disk format, `StorageInterface` method, or
third-party dependency was introduced. The file-dialog filter, caption, and preparing
status text are constants in `collection_messages.py`.

## Observability

Structured `key=value` lines. Names, URLs, headers, bodies, scripts, full candidate
lists, and the status-bar string itself are never logged — an imported collection
routinely carries credentials in a header template. Paths are logged for triage
(user-chosen import file). See `ai-tasks/PYPOST-987/50-observability.md`,
`ai-tasks/PYPOST-1004/50-observability.md`, and
`ai-tasks/PYPOST-1005/50-observability.md`.

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

### Parse / apply / completion (PYPOST-987 / PYPOST-1004)

In `collection_import.py`:

- **INFO** `collection_import_file_parsed path=… candidate_count=… error_count=…`

In `collection_import_actions.py`:

- **WARNING** `collection_import_file_invalid reason=…` — the exception message, or the
  literal `no_valid_collections`
- **INFO** `collection_import_completed added_count=… updated_count=… skipped_count=…
  renamed_count=… request_count=… error_count=…`

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
| Result dialog is unsuccessful and plan counts look higher than the tree | At least one `save_collection` write failed (disk full, permissions, read-only data directory); apply reloaded memory from disk (PYPOST-1004) | Read ERROR `collection_import_save_failed` for failing ids, then WARNING `collection_import_reconciled`; the tree matches durable storage; dialog counts are plan attempts (contract B), not a post-reload recount |
| Imported requests do not send correctly | `{{placeholders}}` are imported verbatim and need their environment | Select the matching environment — see [Environments Dialog](environments_dialog.md) |
| An imported collection appears as `Copy of X` without a prompt | Two entries in the same file shared that name | Expected: in-file duplicates are always renamed, since neither is a collection you already had |
| Result dialog "Renamed" count is lower than the number of `Copy of …` names in the tree | `renamed` was stored as a dict keyed by original name (fixed in PYPOST-1003) | Confirm you are on a build where `CollectionImportPlanResult.renamed` is `list[tuple[str, str]]`; n same-named duplicates should report n−1 renames |
| Agents suddenly see new MCP tools | Imported requests had `expose_as_mcp: true` and a running endpoint selected that collection; `collections_changed` refreshes only those endpoint(s) | Review that collection's MCP flags and endpoint selection before importing — see [MCP Integration](mcp_integration.md) |
| WARNING `collection_import_worker_finish_wait_timeout` | Short post-`finished` join did not complete within `_WORKER_FINISH_WAIT_MS` | Same class of issue as storage gateway finish hygiene (PYPOST-829); usually transient; escalate if paired with crashes under rapid import churn |

## Related

- [Collection Export](collection_export.md) — write a collection to the same JSON shape (PYPOST-989)
- [Collection Storage](collection_storage.md) — the on-disk format this feature reads
- [Collection Loading](collection_loading.md) — the async startup path that shares
  `apply_loaded_collections` and the worker finish-teardown pattern
- [Async Environment Storage](environment_storage_async.md) — sibling `QThread` + finish
  wait hygiene
- [Environments Dialog](environments_dialog.md) — the environment import precedent
- [UI Identity](ui_identity.md) — `COLLECTION_IMPORT_BUTTON` and the widget-id convention
