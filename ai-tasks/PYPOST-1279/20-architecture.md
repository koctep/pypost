# PYPOST-1279: Import from file and connected library architecture

## Architectural intent

Keep collection import decisions and persistence in the existing Qt-free import
planner, while adding a source adapter for connected libraries. The UI chooses a
source and, for library imports, a Copy or Link mode; both paths then use the
same candidate validation, conflict decisions, active-collection update, and
result reporting rules.

The implementation remains additive. Existing callers of
`CollectionsPresenter.import_collections()` continue to reach the file flow,
while the Collections panel exposes explicit `From File` and `From Library`
actions.

## Module boundaries

```text
CollectionsPresenter
  ├─ CollectionsPanel (From File / From Library actions)
  └─ CollectionImportActions
       ├─ collection_item_dialogs (source choice, file picker, conflicts/results)
       ├─ library_collection_import_dialog (library/collection selection + Copy/Link)
       ├─ collection_import (parse, validate, conflict plan, ID reservation)
       ├─ library_collection_import (resolve manifest entries and read candidates)
       └─ collection_import_apply (persist active collections and refresh)

LibraryManagerService
  ├─ connected LibraryConnectionRecord instances
  ├─ manifest discovery and validation
  └─ path-safe resolution of declared collection files
```

`CollectionsPresenter` owns the panel and delegates orchestration. It does not
read library files, decide conflict policy, or mutate a library source.
`CollectionImportActions` owns the GUI-thread sequence and worker lifecycle.
The pure core modules return typed candidates and plans so presenter and dialog
tests do not require Git or a real remote.

## Import sources and candidate model

The existing file parser remains the source for standalone JSON/YAML files. A
library source adapter obtains current records from `LibraryManagerService`,
reads each manifest-declared path relative to the library root, and parses the
file through the same collection deserialization/validation boundary. Paths are
accepted only when they remain under the resolved library directory; malformed,
missing, or unreadable entries become actionable per-item errors.

The adapter returns a typed candidate containing:

- the validated `Collection` payload used by the existing planner;
- the connected library stable ID and manifest identity;
- the manifest-relative collection path and display name;
- source availability and diagnostic information.

The concrete core seam is a `LibraryCollectionImportService` (Qt-free) with
`list_entries(connection)` for selector rows and `resolve_entries(selection)`
for the pre-apply recheck. `list_entries` reads the current manifest and
returns descriptors even when an individual declared file has a diagnostic.
`resolve_entries` reloads the connection by stable ID, reads the manifest again,
and returns validated candidates or per-entry errors. Both methods use one
private path resolver: reject absolute paths and any path with `..`, resolve
against the connection's canonical local root, and require the result to remain
below that root. The resolver then calls the existing
`load_collection_import_candidates` parser, so JSON/YAML shape and Pydantic
validation remain one shared rule. A manifest entry yielding multiple records
is represented as multiple candidates with the same source path and distinct
display labels; an empty or malformed entry is an error, never an empty
collection.

Candidates are resolved immediately before the apply phase. A library that has
been disconnected or changed since the selector opened is re-resolved and
cannot silently become an empty collection. Valid independent selections may
still complete, while failed selections are reported.

## Copy and Link semantics

Copy uses the existing materialization path: it deep-copies collection content,
reserves collection/request/profile IDs, and persists an independent active
collection. It stores no source authority, so later edits affect only the active
copy.

Link adds an optional `LibraryCollectionLink` value to `Collection`, composed of
the library stable ID, manifest ID, and normalized manifest-relative path. This
new Pydantic value is optional, so legacy collection JSON remains compatible;
Copy leaves it `None`. The import service owns `resolve_link(link)`, which
re-resolves the current connection and source path through the same safe parser.
`CollectionsPresenter.refresh_linked_collection(collection_id)` delegates that
operation and asks `RequestManager` to replace the linked collection while
preserving its active collection ID and link metadata. A future startup or
explicit refresh can call the same presenter operation. Missing/disconnected
sources retain the last valid active content and surface a stale/unavailable
diagnostic; they are never replaced with an empty collection. The task does
not add source-edit operations through the active collection.

Conflict handling runs after candidate resolution and before any persistence.
Overwrite preserves the active collection ID; Keep Both reserves new IDs and a
distinct name; Skip changes nothing. A single mode applies to the selected
library candidates, but each conflict remains an explicit user decision.

## UI flow

The import control offers two labeled actions:

1. `From File` opens the existing file picker and asynchronous parse flow.
2. `From Library` opens a modal selector populated from currently connected,
   readable registered and managed-clone records. Each library row exposes its
   bundled collection entries with friendly names or source-path fallbacks.

The selector requires at least one collection and an explicit Copy or Link
choice. Cancel at any dialog stage returns without changing active collections.
The selection dialog is presentation-only: it returns a typed selection and
does not call storage. The presenter passes that selection to the core adapter,
then to the shared conflict/apply sequence.

## Persistence and safety

Only active collections are written through `RequestManager` and its existing
storage interface, extended with an ID-preserving replace seam for Link
refresh. Library source files, Git state, overlays, and connection records are
read-only during import. The library manager/import service boundary remains the
only path-aware boundary for resolving connected libraries.

The planning phase is transactional: no writes occur until source resolution,
mode choice, and conflict decisions finish. Persistence is deliberately
per-item because the existing storage interface can fail for one collection.
`apply_imported_collections` stops or records each failed write according to its
existing result contract; successful earlier writes remain visible in the
result, failed items are not reported as imported, and Link metadata is attached
only to a collection that was actually saved. The UI refreshes the tree only
after the write attempt and reports mixed outcomes. Cancellation before apply
leaves both active collections and source libraries unchanged.

## Threading and observability

File parsing retains the existing `CollectionImportParseWorker`. Library
manifest and collection reads may use the same worker boundary because they can
touch multiple files; dialogs and conflict prompts remain on the GUI thread.
No Qt object crosses into the core adapter or planner. Busy state and timeout
behavior use the existing import action lifecycle. Source kind, mode, outcome,
candidate count, and failure category are safe bounded telemetry labels; local
paths, remote URLs, credentials, and collection payloads are excluded from
logs and metrics.

## Test seams and Step 3 repro plan

Add a focused red repro module, expected at
`tests/test_collection_import_library_pypost_1279_repro.py`, covering:

- distinct panel/menu actions dispatch to File and Library flows;
- a connected registered library and managed clone project their declared
  collections with readable fallback labels;
- Copy materializes independent content and Link persists source metadata;
- multiple selection, conflict decisions, cancellation, unavailable source, and
  mixed-result handling;
- source files and connection records remain unchanged;
- presenter/dialog seams are injectable and no real Git/remote is required.

Existing file-import tests remain the regression suite for JSON/YAML parsing,
conflict policy, async parsing, cancellation, and result feedback.

## Risks and rollout

- The persisted `Collection` model has many legacy callers; link metadata must
  be optional and backward compatible with existing JSON files.
- Manifest entries currently use relative path strings, so path validation must
  happen at the library root and must reject traversal.
- Library refresh can race with disconnect or source edits; re-resolution and
  last-valid-content retention are required before enabling Link.
- The selector must not turn an unavailable or empty library into a successful
  import; diagnostics need to remain distinguishable from ordinary conflicts.

Implementation order is: add core source/link models and resolver, add focused
red repros, implement shared action/dialog wiring, then add observability,
cleanup, documentation, and the final gates.

## Jira traceability

- Jira story: [PYPOST-1279](https://pypost.atlassian.net/browse/PYPOST-1279)
- Requirements: `ai-tasks/PYPOST-1279/10-requirements.md`
