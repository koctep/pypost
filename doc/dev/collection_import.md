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

## Architecture

```text
CollectionsPresenter.panel          Import Collection… button (COLLECTION_IMPORT_BUTTON)
        │
        ▼  delegates
CollectionImportActions             pick → parse → prompt → plan → apply → refresh
        │
        ├─ collection_item_dialogs  QFileDialog + three QMessageBox helpers
        ├─ collection_import        pure: parse, conflicts, id reservation, plan, summary
        └─ collection_import_apply  RequestManager swap + StorageManager writes
```

- **`pypost/core/collection_import.py`** — the pure core. No Qt, no storage. Parses a
  file into candidate `Collection` models, detects name conflicts, reserves colliding
  ids, computes the resulting collection list, and formats the summary text. Directly
  unit-testable without a `QApplication` or a data directory.
- **`pypost/core/collection_messages.py`** — every user-visible string (dialog titles,
  file filter, button label, summary lines, per-record error reasons), mirroring
  `environment_messages.py`.
- **`pypost/core/import_conflicts.py`** — `ImportConflictDecision` and
  `generate_import_copy_name`, extracted from `environment_import.py` so both import
  flows share one conflict vocabulary. `environment_import.py` re-exports them, so no
  environment-side call site changed.
- **`pypost/core/collection_import_apply.py`** — `apply_imported_collections`, the only
  bulk collection-write loop in the codebase. A free function over `RequestManager`'s
  public surface rather than a method on it, which keeps `request_manager.py` inside its
  SOLID audit cap (`scripts/audit_baseline_metrics.py`).
- **`pypost/ui/presenters/collection_import_actions.py`** — `CollectionImportActions`,
  the Qt shell. Sequences the pure core against dialogs and app state. Split out of
  `CollectionsPresenter` the same way `CollectionTreeActions` and `CollectionsAsyncLoader`
  are.
- **`pypost/ui/collection_item_dialogs.py`** — four helpers:
  `prompt_import_collection_file`, `show_collection_import_invalid_file_error`,
  `prompt_collection_import_conflict`, `show_collection_import_result`. The
  Overwrite/Keep Both/Skip message box body is shared with the environment flow through
  the private `_prompt_import_conflict_box`.
- **`pypost/ui/presenters/collections_presenter.py`** — gained a `panel` property. The
  sidebar tab now mounts `presenter.panel` (a `QWidget` holding the tree plus an action
  row) instead of the bare tree; `presenter.widget` still returns the `QTreeView`, so
  existing callers and automation are unaffected.

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

### `format_collection_import_result(result) -> str`

Human-readable summary for the result dialog: counts, the original → new name mapping for
renames, and any per-entry failures.

### `apply_imported_collections(manager, collections, persisted) -> list[str]`

Swaps in the planned list via `RequestManager.apply_loaded_collections` (which rebuilds
`_request_index`) and writes each collection in `persisted`. Returns one formatted message
per collection that could not be written; the loop continues past a failure so one bad
write cannot strand the rest.

Deliberately **not** routed through `RequestManager.create_collection`, which rejects
duplicate names: an import resolves name conflicts through an explicit user decision and
may legitimately produce a name `create_collection` would refuse.

### Testing seam

`CollectionsPresenter.__init__` accepts an optional `read_import_file` callable,
defaulting to `load_collection_import_candidates`. Qt tests inject a stub reader to
exercise the flow without touching disk; the end-to-end test omits it and drives the real
parser, `RequestManager`, and `StorageManager` against a `tmp_path`.

## Configuration

None. No new setting, environment variable, on-disk format, `StorageInterface` method, or
third-party dependency was introduced. The file-dialog filter and caption are constants in
`collection_messages.py`.

## Observability

In `collection_import.py`:

- **INFO** `collection_import_file_parsed path=… candidate_count=… error_count=…`

In `collection_import_actions.py`:

- **WARNING** `collection_import_file_invalid reason=…` — the exception message, or the
  literal `no_valid_collections`
- **INFO** `collection_import_completed added_count=… updated_count=… skipped_count=…
  renamed_count=… request_count=… error_count=…`

In `collection_import_apply.py`:

- **INFO** `collection_import_applied collection_count=… persisted_count=…
  failed_count=…`
- **ERROR** `collection_import_save_failed collection_id=… error=…`

Collection and request **names**, URLs, headers, bodies, and scripts are never logged — an
imported collection routinely carries credentials in a header template. The failed-write
line logs the collection id, not its name. See
`ai-tasks/PYPOST-987/50-observability.md`.

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| "No valid collections found in this file." | The file parsed, but every entry was rejected — most often a foreign format whose root object has no top-level `name` | Check the per-entry reasons listed below the message in the same dialog; export from PyPost or hand-write the documented shape |
| An entry is listed as `Entry 3: missing or empty "name" field` | That record had no usable `name`, so it could not be labelled | `name` is the one required field on a collection record |
| Import succeeded but the result dialog says it was unsuccessful | At least one `save_collection` write failed (disk full, permissions, read-only data directory) | Read the `collection_import_save_failed` ERROR lines for the failing ids; in-memory state is ahead of disk for those collections until the next successful save |
| Imported requests do not send correctly | `{{placeholders}}` are imported verbatim and need their environment | Select the matching environment — see [Environments Dialog](environments_dialog.md) |
| An imported collection appears as `Copy of X` without a prompt | Two entries in the same file shared that name | Expected: in-file duplicates are always renamed, since neither is a collection you already had |
| Agents suddenly see new MCP tools | Imported requests had `expose_as_mcp: true`; the flow emits `collections_changed`, which re-registers tools without a restart | Review a shared collection's MCP flags before importing — see [MCP Integration](mcp_integration.md) |

## Related

- [Collection Storage](collection_storage.md) — the on-disk format this feature reads
- [Collection Loading](collection_loading.md) — the async startup path that shares
  `apply_loaded_collections`
- [Environments Dialog](environments_dialog.md) — the environment import precedent
- [UI Identity](ui_identity.md) — `COLLECTION_IMPORT_BUTTON` and the widget-id convention
