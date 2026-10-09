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
`tests/test_collection_import_profile.py`. **PYPOST-1263** changed the large-dataset planner
benchmark to gate on a current-thread CPU-work budget instead of wall time; see
[Planner CPU-work benchmark](#planner-cpu-work-benchmark-pypost-1263).

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
and best-effort: a reader must call `on_progress` to be interruptible, and one expensive record
or an uninterruptible native operation can delay observation. No forcible termination is used.

**PYPOST-1266** makes that cancellation contract explicit for every background file reader.
`ReadImportFile` is a structural protocol requiring the `on_progress` keyword. The worker calls
the reader once with its checkpoint, without signature inspection or a no-callback fallback.
Supported functions, bound methods, callable objects, and opaque callables all use the same
checkpoint path; single-argument readers must be migrated. The production parser retains its
optional callback for synchronous callers. Focused contract tests cover reader shapes, cancellation,
and real JSON parsing without changing the conflict/apply workflow or decoding latency guarantee.

**PYPOST-1267** adds preparation checkpoints during production file loading and JSON/YAML
decoding, including YAML fallback and long scalar values. Direct callbacks receive `(0, 0)`
before record totals are known; the worker consumes these checks without emitting GUI progress.
See [Preparation checkpoints](#preparation-checkpoints-pypost-1267) for measured latency and limits.

**PYPOST-1230** extracts the repeated presenter-import wait used by the collection-import UI tests
into the test-only `tests/helpers/collection_import_wait.py` module. It does not add a production
dependency or change the import lifecycle; it centralizes the test condition that an expected
outcome is visible and the presenter has become idle.

**PYPOST-1279** adds separate **From File** and **From Library** routes. The library route
discovers collections declared by connected registered libraries and managed clones, lets the
user select one or more entries, and asks whether the selected entries should be copied or linked.
Library imports reuse the same validation, conflict, persistence, and result-summary contracts as
file imports.

## Library-backed import (PYPOST-1279)

### Architecture

```text
CollectionsPresenter
        │
        ├─ From File ─────── CollectionImportActions ── CollectionImportParseWorker
        │
        └─ From Library ──── CollectionImportActions ── LibraryOperationWorker
                                      │
                                      └─ LibraryCollectionImportService (Qt-free)
                                             ├─ list_entries()
                                             ├─ resolve_entries()
                                             └─ materialize_candidate()
```

`LibraryCollectionImportService` reads the library manifest and delegates collection parsing to
`load_collection_import_candidates`. It never writes to a library source. The UI performs listing
and selected-entry resolution in `LibraryOperationWorker`; conflict prompts and active-collection
persistence remain on the GUI thread and use `plan_collection_import` plus
`apply_imported_collections`.

### Usage and API

The service is injectable and does not require Qt:

```python
service = LibraryCollectionImportService(library_manager=library_manager)
entries = service.list_entries()
selected = [entry for entry in entries if entry.error is None]
resolution = service.resolve_entries(selected)
linked = [
    service.materialize_candidate(candidate, LibraryImportMode.LINK)
    for candidate in resolution.candidates
]
```

`LibraryCollectionImportEntry` identifies a source with `library_id`, optional `manifest_id`, a
normalized relative `collection_path`, and `collection_index` for a selected record in a bundled
file. `LibraryCollectionImportResolution` keeps valid candidates and per-entry errors separate so
one unavailable or malformed selection does not hide valid siblings.

### Copy and Link semantics

- **Copy** deep-copies the selected collection and clears library metadata. Later source changes
  do not affect the active collection.
- **Link** deep-copies the selected content and persists `Collection.library_link`, including the
  library identity, manifest identity, relative path, and bundled-record index. The source remains
  read-only. `LibraryCollectionImportService.refresh_linked_collection()` re-resolves the recorded
  source and preserves the active collection ID.
- Both modes use the existing name-conflict choices: Overwrite, Keep Both, or Skip. Planning is
  completed before any active collection is written.

### Manifest and path safety

Only registered and cloned connections are considered. A manifest collection entry must resolve
under the canonical connected-library root. Absolute paths, drive-qualified paths, backslashes,
and `..` traversal are rejected both while listing and immediately before applying a selection.
If a manifest, source file, or selected record disappears after listing, the active collection
manager does not receive that unavailable selection and the user receives a bounded diagnostic;
valid sibling selections may still be applied, while an entirely invalid selection leaves the
active manager unchanged.

### Troubleshooting

| Symptom | Check |
| --- | --- |
| **From Library** shows no usable entries | Confirm the connection has a readable `pypost-library.yaml`/`.yml` manifest and that its declared files exist under the library root. |
| One entry is unavailable | Read the per-row diagnostic; another valid manifest entry can still be selected. |
| Import reports a source changed or unavailable | Reopen the library picker to refresh the manifest view; selections are revalidated before writes. |
| A Link refresh loads the wrong content | Confirm the persisted link includes `collection_index` for bundled files, then retry the refresh. |
| Copy unexpectedly tracks source changes | Re-import with **Copy**; only **Link** stores `Collection.library_link`. |

Library import lifecycle events are logged with bounded counts, modes, IDs, and exception types.
The existing `gui_library_operations_total` metric records `collection_import_file`,
`collection_import_library`, and `collection_import_refresh` outcomes.

## Architecture

```text
CollectionsPresenter.panel          Import Collection… button (COLLECTION_IMPORT_BUTTON)
        │
        ▼  delegates
CollectionImportActions (QObject)   pick → async parse → prompt → plan → apply → refresh
        │
        ├─ CollectionImportParseWorker  QThread: reader(path, on_progress=checkpoint)
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
- **`pypost/core/collection_import_lifecycle_policy.py`** — Qt-free
  `CollectionImportLifecyclePolicy` (every wait and teardown limit) and
  `ImportTeardownDeadline` (one monotonic deadline shared by the teardown phases). See
  [Teardown lifecycle policy](#teardown-lifecycle-policy-pypost-1264) (PYPOST-1264).
- **`pypost/core/collection_import.py`** — the pure core. No Qt, no storage. Parses a
  file into candidate `Collection` models, detects name conflicts, reserves colliding
  ids, computes the resulting collection list, recounts plan results against save
  failures (`recount_collection_import_plan`), and formats the summary text. Directly
  unit-testable without a `QApplication` or a data directory. Called from the parse
  worker via the injected `ReadImportFile` implementation (default
  `load_collection_import_candidates`).
- **`pypost/core/collection_import_decode.py`** — Qt-free UTF-8 reading and instance-local
  cooperative JSON and safe YAML decoders. Used during preparation when a callback is supplied;
  synchronous calls without a callback retain standard-library JSON and PyYAML decoding.
- **`pypost/core/qt/collection_import_parse_worker.py`** —
  declares the structural `ReadImportFile` protocol and owns `CollectionImportParseWorker`
  (`QThread`). Calls `reader(path, on_progress=checkpoint)` off the GUI thread without signature
  inspection or fallback; emits `parse_completed(collections, parse_errors)`, `parse_failed(error)`, or
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
  for the preparing cue; types the optional `read_import_file` DI seam as `ReadImportFile | None`.
  Exposes `wait_import_idle()` and `teardown()` delegating to `CollectionImportActions` for clean
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
4. Worker calls the reader off-thread with the required `on_progress` keyword; emits completed,
   failed, or cancelled.
5. If teardown requests interruption, the worker normally exits through `parse_cancelled`;
   however, the final best-effort publication race can still result in `parse_completed` if
   interruption arrives between the final check and emission. In the normal cancellation path,
   the orchestrator returns to `IDLE` without applying or displaying a result.
6. For completion or failure, the orchestrator clears the cue, then on the GUI thread either
   shows the invalid-file dialog or runs conflict prompts → `plan_collection_import` →
   `apply_imported_collections` → refresh → result dialog.
7. Worker `finished` slot: `deleteLater` + bounded `wait(worker_finish_join_ms)` (100 ms,
   PYPOST-829 hygiene; WARNING if the short join times out). See
   [Teardown lifecycle policy](#teardown-lifecycle-policy-pypost-1264).

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
    W->>R: reader(path, on_progress=checkpoint)
    R-->>W: on_progress(0, 0) during preparation
    W->>W: Check interruption; suppress progress signal
    R-->>W: on_progress(done, total) for a record
    W->>W: Emit parse_progress; check interruption
    UI->>W: requestInterruption() during teardown
    W-->>UI: parse_cancelled()
    UI->>UI: Set IDLE; clear cue; discard parse result
```

Every supported reader must invoke the supplied checkpoint at its existing safe record boundaries
and let callback exceptions propagate immediately. The production reader,
`load_collection_import_candidates`, invokes `on_progress(done, total)` once per record, including
invalid records, and sends `(0, 0)` during preparation (PYPOST-1267). The worker checks interruption
and returns without a progress signal for `(0, 0)`. For real record progress it first emits
`parse_progress` and then checks `isInterruptionRequested()`. If the flag is set, an internal
`CollectionImportCancelled`
exception unwinds the reader call into `run()`, which catches it and emits exactly one
`parse_cancelled()` signal. A final check after the reader returns narrows, but does not
eliminate, the publication race: if interruption is observed after the last progress callback,
it prevents `parse_completed`, but interruption can still arrive between this check and
`parse_completed.emit()`.

`CollectionImportActions.teardown()` requests interruption before entering `wait_idle()`. The
wait pumps the Qt event loop when one exists so the cancellation signal and worker completion can
be delivered; any remaining running worker receives a final guarded request and a join bounded
by `min(final_join_ms, remaining budget)` (see
[Teardown lifecycle policy](#teardown-lifecycle-policy-pypost-1264)). After that bounded join
attempt, the worker reference is cleared and the action state is forced to `IDLE`, even if the
join times out. This is a cooperative stop, not a kill: a reader
blocked in I/O or decoding may still be running after the wait and cause teardown to return
`False` with a timeout warning.

### Preparation checkpoints (PYPOST-1267)

With a callback, `load_collection_import_candidates` delegates preparation to
`collection_import_decode.read_import_document(path, checkpoint=None)`. The callback remains
optional for synchronous use; the worker always supplies it through the existing required
`ReadImportFile.on_progress` keyword. No second cancellation argument is required of injected
readers. `(0, 0)` means preparation is active and record totals are unknown; it does not mean
validation is complete or provide a byte percentage. Direct consumers should filter this sentinel
before calculating record progress. Positive counts remain one update per record, including invalid
records, in input order.

UTF-8 text reads use chunks of at most 64 Ki characters with checks before and after each read.
The JSON decoder uses bounded 4096-character lexical windows for strings, keys, numbers, and
whitespace, plus an explicit container stack with checks during descent and unwinding. The safe
YAML loader checks printable input and forwarding in bounded windows, every 4096 lookahead calls,
and at composition/construction boundaries. Merge assembly checks each source/sequence member and
each batch of at most 4096 entries. Root list validation also checks every 4096 entries. Parsing
state belongs to each invocation; cancellation does not modify global parser functions.

The iterative JSON path preserves successful 600/900-level standard-decoder inputs without
changing the process recursion limit. It can also accept deeper valid JSON that `json.loads()`
would reject with `RecursionError`. This broader acceptance does not guarantee arbitrary-depth
collection-model validation. Python or PyYAML upgrades should rerun the differential coverage in
`tests/test_collection_import_decode.py`; the adapted parser behavior and upstream licenses are
kept in the helper. Detailed implementation decisions are in the
[task architecture](../../ai-tasks/PYPOST-1267/20-architecture.md).

#### Format selection, exceptions, and cleanup

`.yaml`/`.yml` files use safe YAML decoding. Other suffixes try JSON first; only a JSON syntax
failure triggers YAML fallback. Fallback accepts an object or list, and otherwise preserves the
original JSON error, including when YAML raises an ordinary constructor exception such as an
invalid timestamp `ValueError`. Direct YAML constructor `ValueError` still propagates unchanged;
ordinary YAML syntax errors retain their file-error translation.

The reader protects preparation callbacks with a private exception carrier before entering I/O
translation or fallback. It unwraps outside those scopes, preserving the original callback
exception object and traceback, including `OSError`, `ValueError`, `yaml.YAMLError`, and worker
cancellation. Callback errors must never trigger YAML retry or become file/record errors. File
handles close through a context manager; YAML loaders are disposed in `finally`, including
interruption during initialization. The helper's optional `checkpoint` parameter is an internal
seam: callers integrating it with broad parser-error translation must use the same origin
protection. Application callers should use `load_collection_import_candidates`.

#### Measured cancellation bound and regression usage

The accepted regression limit is **1000 ms from interruption request until the worker stops**
on the normal test environment with readable local files. All 11 real-file cases use inputs of
at least 16 MiB (16,777,242–17,351,716 bytes). They request cancellation during observed active
loading or lexical scanning, then allow actual work before the next production checkpoint;
pre-start cancellation and completed decoding do not satisfy these checks. Scenarios include
JSON, YAML, fallback YAML, bundles, and retained large text values with plain/quoted YAML scalars.

The final PYPOST-1267 run recorded loading at **1.197–1.985 ms**, JSON scanning at
**0.412–0.636 ms**, and YAML/fallback scanning at **0.295–0.832 ms**. The run exported fixture
bytes, phase, shape, format, limit, and measured latency to `/tmp/PYPOST-1267-latency.xml`.
That temporary report is execution evidence, not a required repository artifact. Reproduce the
focused checks through Make:

```bash
make test WORKERS=1 WORKER_TIMEOUT=180 \
  PYTEST_ARGS="tests/test_collection_import_decode_cancellation.py"
make test WORKERS=1 WORKER_TIMEOUT=60 \
  PYTEST_ARGS="tests/test_collection_import_decode.py tests/test_collection_import_progress.py"
```

The measurements exclude operating-system/storage stalls, resource exhaustion, and abnormal
scheduling; they are not a hard real-time guarantee for arbitrary inputs. Native allocations,
final joins/list assembly, numeric conversion, and inherited YAML scalar resolver/constructor
work cannot be interrupted mid-operation. One expensive model-validation record can still delay
its next checkpoint. The whole text and decoded tree remain in memory with temporary chunk/string
pieces; no streaming-memory, throughput, maximum-file-size, or arbitrary-depth guarantee is added.

### Teardown lifecycle policy (PYPOST-1264)

Every wait and teardown limit used by collection import is in one named, Qt-free policy:
`pypost/core/collection_import_lifecycle_policy.py`. Before PYPOST-1264 these were the literals
`5000` (default `timeout_ms`), `100` (final join and `_WORKER_FINISH_WAIT_MS`) and `10` (no-app
poll), and the teardown phases each had their own budget, so `teardown(B)` could take about
`2 * B + 100` ms. Design and decisions:
[PYPOST-1264 requirements](../../ai-tasks/PYPOST-1264/10-requirements.md),
[architecture](../../ai-tasks/PYPOST-1264/20-architecture.md) and
[technical debt](../../ai-tasks/PYPOST-1264/60-tech-debt.md).

#### Policy module

- **`CollectionImportLifecyclePolicy`** — frozen dataclass of millisecond limits. Its
  `__post_init__` raises `ValueError` if a field is not a non-negative `int` (`bool` is rejected)
  or if `final_join_ms`, `worker_finish_join_ms` or `idle_poll_ms` is larger than
  `teardown_budget_ms`. `resolve_budget_ms(timeout_ms)` returns `teardown_budget_ms` for `None`
  and `max(0, int(timeout_ms))` otherwise, so a negative budget becomes 0.
- **`DEFAULT_COLLECTION_IMPORT_LIFECYCLE_POLICY`** — the default instance (values below).
- **`ImportTeardownDeadline`** — one monotonic deadline. `start(budget_ms, clock=time.monotonic)`
  starts it; `budget_ms`, `elapsed_ms()`, `remaining_ms()`, `bounded(limit_ms)` (=
  `min(limit_ms, remaining_ms())`) and `expired` (no whole millisecond left) read it. Values are
  computed from whole microseconds and truncated to milliseconds, never rounded up, so float
  noise such as `1000.1 - 1000.0` cannot change a result.
- **`Clock`** — type alias `Callable[[], float]` (seconds) for the injectable clock.

| Field | Default (ms) | Purpose |
| --- | --- | --- |
| `teardown_budget_ms` | 5000 | Caller budget for `wait_idle` / `teardown` if none is passed |
| `final_join_ms` | 100 | File-worker join after disconnect, capped by the remaining budget |
| `worker_finish_join_ms` | 100 | Join after a normal `QThread.finished`; not capped |
| `idle_poll_ms` | 10 | No-`QApplication` `wait_idle` poll slice, capped by remaining |
| `budget_tolerance_ms` | 50 | Allowed teardown wall-time overrun on an unloaded machine |

Rationale for the defaults:

- `teardown_budget_ms` keeps the inherited 5000 ms. It matches the main-window shutdown default,
  is long enough for a cooperative parse cancel, and keeps shutdown bounded. The measurement below
  showed no reason to change it.
- `final_join_ms` gives native `QThread` exit a short grace after interruption. Because it is
  capped by the remaining budget, it can no longer extend the budget.
- `worker_finish_join_ms` keeps the PYPOST-829 H3 value. It runs on the GUI thread, so it must
  stay small; outside teardown there is no caller budget to cap it with.
- `idle_poll_ms` names the former bare `wait(10)` literal.
- `budget_tolerance_ms` is a contract value only: it is not a wait, only `__post_init__`
  validates it, and no CI test asserts it. 50 ms is well below the 100 ms final join and the
  `2 * B` overrun it replaces.

#### One shared deadline

`teardown(timeout_ms)` starts one `ImportTeardownDeadline` and runs its phases in order. Every
phase wait is taken from what is left of that deadline:

1. **P0** — if busy and the file worker is running, `requestInterruption()` (no wait).
2. **P1** — if busy, wait for idle until the deadline expires (`_wait_idle_until(deadline)`).
3. **P2** — disconnect the file worker's signals; if it still runs, request interruption again and
   `wait(min(final_join_ms, remaining))`; then `deleteLater()` and clear the reference.
4. **P3** — if the library worker runs, `wait(remaining)`; then disconnect, `deleteLater()` and
   clear the reference. The library worker cannot be interrupted (design Risk 4,
   [PYPOST-1324](https://pypost.atlassian.net/browse/PYPOST-1324)).
5. **P4** — set `IDLE`, run one `processEvents()`, log `collection_import_teardown_completed`.

The sum of the deadline-bounded waits (P1, P2, P3) never exceeds the caller budget. Once the
budget is used up, P2 and P3 issue only `wait(0)` probes and teardown returns `False`. Public
`wait_idle(timeout_ms)` starts its own deadline the same way. Two documented exceptions are not
bounded by the deadline:

- **Nested worker-finish join** — if `_on_worker_finished` runs inside P1's `processEvents()`, its
  `wait(worker_finish_join_ms)` is uncapped (design Risk 3). `finished` is emitted after `run()`
  returns, so this join is normally instant, and probing with `wait(0)` could reap a thread that
  is still exiting. Test coverage is [PYPOST-1322](https://pypost.atlassian.net/browse/PYPOST-1322).
- **Long queued GUI slots** — a slot that runs inside a `processEvents()` call (for example an
  apply) is only checked against the deadline when it returns.

Outside those exceptions, teardown wall time is expected to stay within `timeout_ms +
budget_tolerance_ms` on an unloaded machine. The tolerance covers work outside the waits: the
last `processEvents()` pass, disconnects, `deleteLater`, logging and millisecond rounding. This
is a documented contract checked by the slow latency module, not a runtime check.

#### Constructor parameters and presenter delegation

`CollectionImportActions.__init__` takes two keyword-only parameters (after `parent`):

- `lifecycle_policy: CollectionImportLifecyclePolicy | None = None` — `None` uses
  `DEFAULT_COLLECTION_IMPORT_LIFECYCLE_POLICY`. Read it back with the `lifecycle_policy` property.
- `clock: Clock | None = None` — `None` uses `time.monotonic`. This is a test seam: it is passed
  to every `ImportTeardownDeadline.start`, so a fake clock makes the wait arithmetic exact.

`wait_idle(timeout_ms: int | None = None)` and `teardown(timeout_ms: int | None = None)` resolve
`None` through the policy. `CollectionsPresenter.wait_import_idle` and
`CollectionsPresenter.teardown` keep the same `None` default and pass `timeout_ms` through
unchanged; the presenter resolves it only for its own `collections_presenter_teardown_started
timeout_ms=%d` log line (`self._import_actions.lifecycle_policy.resolve_budget_ms(timeout_ms)`).
The presenter does not take a policy; it always uses the actions' default.

#### Preserved behaviour

- Cooperative interruption only; no `QThread.terminate()` fallback.
- Signals are disconnected before the file worker is joined and reaped; the reference is cleared
  and the state forced to `IDLE` even after a join timeout.
- Teardown is idempotent: a second call on an idle action returns `True` without waiting.
- Event names and levels are unchanged; PYPOST-1264 only appended fields (see
  [Observability](#observability)).
- The `_on_worker_finished` join keeps its 100 ms value and is still uncapped.
- Explicit `timeout_ms` values from callers mean the same thing as before: an overall budget.
  The difference is that P2 and P3 no longer add time on top of it, so callers that relied on
  the old extra 100 ms grace need a larger budget (for example the cancellation repro moved
  from 150 to 1000 ms).

#### Tests

- **`tests/test_collection_import_lifecycle_policy.py`** (Qt-free, `timeout(10)`) — defaults,
  `resolve_budget_ms`, immutability, `ValueError` cases, deadline arithmetic and truncation.
- **`tests/test_collection_import_teardown_policy.py`** (fake clock and spy workers,
  `timeout(30)`) — an injected policy drives the default waits; a deadline used up in P1 leaves
  only `wait(0)` probes; no-app poll slices; idle teardown is clean and idempotent; the presenter
  resolves `None` to 5000; exact log fields via `caplog`.
- **`tests/test_collection_import_teardown_budget_repro.py`** (Step 3 repro, `timeout(30)`) —
  test A (`test_teardown_requested_waits_fit_caller_budget`, spies whose `wait(ms)` really
  sleeps): requested waits sum to at most the budget; test B
  (`test_teardown_wait_arithmetic_with_fake_clock`): exact P2/P3 values; and the loose
  real-thread guard below.
- **`tests/test_collection_import_teardown_latency.py`** (`slow`, `timeout(120)`) —
  measurement only: N = 20 per scenario, writes min/p50/p95/max; asserts only `n` and `clean`.

The deterministic tests use the `clock=` seam and spy workers, so they do not depend on machine
load. The only real-thread wall-time assertion in the fast suite is
`test_teardown_real_threads_stay_within_loose_bound`: with both workers blocked, teardown must
finish in under `2 * B` for `B = 300` and under 100 ms for `B = 0` (the old code took about
`2 * B + 100`). During the timed `teardown(...)` call it sets the
`pypost.ui.presenters.collection_import_actions` logger `disabled` and restores it in `finally`.
Under parallel `make test`, pytest live logging (`log_cli = true`, `log_cli_level = "WARNING"` in
`pyproject.toml`) cost up to about 400 ms per WARNING record, and teardown emits several, so the
guard measured logging rather than teardown. CI already passes `-o log_cli=false` (PYPOST-671).
The workaround is removed when [PYPOST-1326](https://pypost.atlassian.net/browse/PYPOST-1326)
fixes local live logging. Log content is asserted in `test_collection_import_teardown_policy.py`.

Run the fast modules and the slow measurement through Make:

```bash
make test WORKERS=1 PYTEST_ARGS="tests/test_collection_import_lifecycle_policy.py \
  tests/test_collection_import_teardown_policy.py \
  tests/test_collection_import_teardown_budget_repro.py"
make test-slow PYTEST_ARGS="tests/test_collection_import_teardown_latency.py -m slow -s"
```

`make test` excludes the latency module (`-m "not slow"` by default). `make test-slow` runs
pytest directly on one process; `-s` shows the printed environment and percentile lines.

#### Measured latency and configurability decision

Measured with `make test-slow PYTEST_ARGS="tests/test_collection_import_teardown_latency.py -m
slow -s"` (one worker; N = 20 per scenario; default 5000 ms budget except the reference row).
Environment: Linux 6.8.0-117 aarch64, 6 CPUs, Python 3.13.5, PySide6/Qt 6.11.1,
`QT_QPA_PLATFORM=offscreen`, load average 0.10 / 0.30 / 0.19 before and 0.08 / 0.29 / 0.19
after.

| Scenario | min | p50 | p95 | max | clean |
| --- | --- | --- | --- | --- | --- |
| Idle | 0.03 | 0.04 | 0.06 | 0.19 | 20/20 |
| Active file import cancelled | 2.19 | 2.34 | 2.43 | 2.45 | 20/20 |
| Active library operation (200 ms) | 202.12 | 204.99 | 208.71 | 211.59 | 20/20 |
| Reference: blocked library op, 100 ms budget | 100.49 | 104.81 | 111.05 | 111.17 | 0/20 |

Times in ms. Decision rule (fixed before measuring): keep fixed policy values if idle p95 ≤ 5 ms,
file-cancel p95 ≤ 25 % of `teardown_budget_ms` (1250 ms), and every run of the first three
scenarios is clean and within `budget + tolerance`. All hold (0.06 ms, 2.43 ms, max 211.59 ms ≤
5050 ms); the reference run also stays within `100 + 50` ms. **Outcome: the limits stay fixed
policy values**; there is no user-visible setting or environment variable. A different policy
can still be injected through `lifecycle_policy` if a future caller needs it.

The evidence comes from one machine and is not re-run automatically (the module asserts only
structure). Re-run the command above and compare against the rule after any change to teardown,
the worker shutdown path or the policy values.

#### Scope limits

- Application shutdown does not call `CollectionsPresenter.teardown`: the presenter is not in the
  main-window teardown owner list (`pypost/ui/main_window_lifecycle.py`), so closing the app
  during an import is not covered by this budget
  ([PYPOST-1321](https://pypost.atlassian.net/browse/PYPOST-1321)). The main-window 5000 ms
  literals are not part of this policy
  ([PYPOST-1325](https://pypost.atlassian.net/browse/PYPOST-1325)).
- Other components still have their own `_WORKER_FINISH_WAIT_MS = 100`
  ([PYPOST-1323](https://pypost.atlassian.net/browse/PYPOST-1323)).
- One test patches the private `_wait_idle_until`, and no runtime code reads
  `budget_tolerance_ms`
  ([PYPOST-1327](https://pypost.atlassian.net/browse/PYPOST-1327)).

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
- **on_progress**: Optional callback invoked as `on_progress(0, 0)` during preparation and
  `on_progress(done, total)` once per record. Filter `(0, 0)` when displaying record progress.
  It remains optional for synchronous core and library callers. The background worker always
  supplies it as its cooperative cancellation checkpoint, including for invalid records.
- **Returns**: candidate collections, and one formatted message per rejected record.
- **Raises**: `CollectionImportFileError` for file-level problems only.
  Exceptions from `on_progress` propagate without becoming per-record validation errors; the
  worker catches its internal cancellation exception and emits `parse_cancelled`.

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

### `ReadImportFile` (PYPOST-1266)

The dependency boundary is declared in `pypost/core/qt/collection_import_parse_worker.py`:

```python
class ReadImportFile(Protocol):
    def __call__(
        self,
        path: Path,
        /,
        *,
        on_progress: Callable[[int, int], None],
    ) -> tuple[list[Collection], list[str]]: ...
```

`path` is positional-only in the protocol so an implementation may name it `_path` without
affecting compatibility. `on_progress` is a required keyword at the worker boundary. An
implementation may give the callback an optional default, as the production parser does, provided
it accepts the supplied keyword and invokes it at safe record checkpoints. Callback exceptions
must unwind immediately; do not catch them as record errors or continue processing after them.

The protocol is structural: no inheritance, registration, or runtime protocol check is needed.
Supported shapes include keyword-only and positional-or-keyword callback functions, bound methods,
callable objects, and correctly typed `**kwargs` forwarding. Opaque callable metadata, including
unavailable `__signature__` information, does not affect compatibility because the worker does not
inspect it. A positional-only callback, a differently named keyword without forwarding, or a
single-argument reader is unsupported. Typing describes call compatibility; contract tests verify
the checkpoint behavior.

### `CollectionImportParseWorker`

Background `QThread` that, after its pre-read interruption guard passes, calls the injected reader
exactly once as `reader(path, on_progress=checkpoint)` and emits:

- `parse_completed` — `(list[Collection], list[str])` candidates and per-record errors
- `parse_failed` — `CollectionImportFileError` or an unexpected `Exception`
- `parse_cancelled` — no payload; the worker observed a requested interruption before
  completion could be published

Workers are one-shot. On `finished`, `CollectionImportActions` schedules `deleteLater`
and a short `wait(worker_finish_join_ms)` (100 ms) before dropping the reference (same
PYPOST-829 pattern as [Collection Loading](collection_loading.md) /
[Async Environment Storage](environment_storage_async.md)).
`parse_cancelled` is mutually exclusive with `parse_completed` and `parse_failed` for one
worker run. It is emitted only for cooperative interruption observed by the worker; it is not
an error signal.

A reader that cannot accept `on_progress` raises `TypeError` during argument binding. The existing
unexpected-exception handler logs the error and emits `parse_failed(TypeError)`; it never retries
without the callback. For a single-argument function, its body does not execute.

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
- **`lifecycle_policy -> CollectionImportLifecyclePolicy`** (property) — the policy that sets
  every wait limit (PYPOST-1264).
- **`wait_idle(timeout_ms: int | None = None) -> bool`** — `None` uses the policy
  `teardown_budget_ms` (5000 ms). While the action is busy, pumps the Qt
  event loop (`QApplication.processEvents()`) or performs short worker waits
  (`min(idle_poll_ms, remaining)`) when no `QApplication` exists until `is_busy()` becomes
  `False`. The event-loop passes allow queued
  parse, result, and worker-cleanup handlers to run, but this method does not explicitly call
  `QThread.wait()` on the `QApplication` path or guarantee that `finished` has been processed
  and the worker reaped when it returns. It performs one additional event-loop pass after idle
  to allow deferred deletion (`deleteLater()`) to run. Returns `True` if idle is observed within
  `timeout_ms`, or `False` if the bounded wait expires (PYPOST-1182, PYPOST-1148).
- **`teardown(timeout_ms: int | None = None) -> bool`** — coordinates interruption, signal
  disconnection, bounded waiting, and worker cleanup (PYPOST-1148). `None` uses the policy
  `teardown_budget_ms`. All waits below share one deadline of that budget (PYPOST-1264; see
  [Teardown lifecycle policy](#teardown-lifecycle-policy-pypost-1264)):
  1. If the worker is running, requests interruption before waiting so an in-flight parse can
     reach its next checkpoint.
  2. If `is_busy()`, waits for idle on the shared deadline (`_wait_idle_until(deadline)`, the
     same loop as `wait_idle()`) to process events while cancellation or completion settles.
     The idle wait does not synchronously join or reap on the `QApplication` path.
  3. Safely disconnects all worker Qt signals (`parse_progress`, `parse_completed`,
     `parse_failed`, `parse_cancelled`, `finished`) within guarded `try...except
     (RuntimeError, TypeError)` blocks, preventing callbacks from firing on a dying presenter.
  4. If the worker remains active, requests interruption again and waits
     `min(final_join_ms, remaining)` for thread exit (`wait(0)` once the budget is used up).
     This final join can time out.
  5. After that bounded join attempt, schedules `worker.deleteLater()` and clears
     `self._worker = None`, even if the join timed out.
  6. If a library worker exists, waits `remaining` for it if it is running (no interruption;
     PYPOST-1324), then disconnects, schedules `deleteLater()` and clears the reference.
  7. Resets the state to `IDLE` and flushes pending Qt events via `app.processEvents()` to
     process deferred deletions.
  Returns `True` if no bounded wait timed out, or `False` if the idle wait, final join or
  library join timed out. A `False` result does not prevent the reference/state cleanup in
  steps 5–7.
- **`import_collections() -> None`** — pick file; dispatch async parse; finish on the
  GUI thread when ready. Callers and the button wire-up do not change.

Constructor DI (beyond the original refresh/emit hooks): optional `show_status` /
`clear_status` for the preparing message; `read_import_file: ReadImportFile` for the worker.
Supply a reader meeting the protocol above, including its checkpoint and exception obligations.
Keyword-only `lifecycle_policy: CollectionImportLifecyclePolicy | None = None` (default policy)
and `clock: Clock | None = None` (`time.monotonic`; test seam for the teardown deadline) were
added by PYPOST-1264.

### `CollectionsPresenter.wait_import_idle(timeout_ms: int | None = None) -> bool`

Delegates directly to `CollectionImportActions.wait_idle(timeout_ms)`; `None` uses the import
lifecycle policy budget (5000 ms). Allows UI harnesses, parent
presenters, and automated test fixtures to wait, within a bound, for the import action to report
`IDLE` while giving queued Qt lifecycle handlers an opportunity to run. It does not itself
guarantee that the native worker has been joined and reaped; call `teardown()` before destroying
widgets or closing panels (PYPOST-1182).

### `CollectionsPresenter.teardown(timeout_ms: int | None = None) -> bool`

Deterministically tears down import actions and presenter resources (PYPOST-1148). Delegates to
`self._import_actions.teardown(timeout_ms=timeout_ms)` and closes the presenter panel
(`self._panel.close()`). `None` uses the import lifecycle policy budget; the presenter resolves
it only to log `collections_presenter_teardown_started timeout_ms=<budget>`. Application
shutdown does not call this method yet
([PYPOST-1321](https://pypost.atlassian.net/browse/PYPOST-1321)). Returns `True` if background
worker resources were cleanly drained and stopped. Test fixtures and parent widget cleanup
routines invoke `teardown()` in `finally:` blocks to prevent background thread leaks and C++
destructor futex deadlocks during test suite runs.

Presenter integrations should call `wait_import_idle()` before making assertions that depend on
parse completion, and call `teardown()` before closing the panel or destroying its parent. Do not
replace this lifecycle with `QThread.terminate()` or direct result application: the action owns
signal disconnection, cooperative interruption, bounded joining, and the cancellation terminal
state.

### Testing seam

`CollectionsPresenter.__init__` accepts `read_import_file: ReadImportFile | None`,
defaulting to `load_collection_import_candidates`. Qt tests inject a compatible stub reader to
exercise the flow without touching disk; the end-to-end test omits it and drives the real
parser, `RequestManager`, and `StorageManager` against a `tmp_path`.

Because parse is async, UI tests must wait for completion rather than asserting immediately after
`import_collections()`. Use the shared `wait_import()` helper below for the normal outcome-plus-idle
contract. Stubs used from the worker thread must be thread-safe, accept `on_progress`, and let
checkpoint exceptions propagate. Record-processing stubs must invoke the checkpoint; a file-error
stub that fails before any record exists need not emit synthetic progress.

### Reader contract regression coverage (PYPOST-1266)

`tests/test_collection_import_reader_contract.py` covers successful results/progress and
first-checkpoint cancellation for all six supported shapes, including opaque callable metadata.
Its original opaque-reader regression verifies exactly one cancellation signal, one processed
record, and no completion or failure. Production JSON cases exercise valid and invalid records,
checking normal candidates/errors/progress and cancellation at either record without publication.

`tests/test_collection_import_progress.py` verifies that a legacy single-argument reader is rejected
with `TypeError` before its body runs, with no completion or cancellation and the existing ERROR
log. Run the focused checks through Make:

```bash
make test WORKERS=1 WORKER_TIMEOUT=60 \
  PYTEST_ARGS="tests/test_collection_import_reader_contract.py \
    tests/test_collection_import_progress.py"
```

The contract module uses an explicit 30-second test timeout, direct-connected signal capture for
deterministic checkpoint interruption, and bounded 5000 ms worker waits/cleanup. The progress
module has a 60-second test timeout. These checks supplement existing presenter cancellation and
final-publication guard tests. The former legacy-success expectation is now rejection coverage.
PYPOST-1265 adds real YAML and lifecycle coverage; see
[Cancellation test layout](#cancellation-test-layout-pypost-1265).

### Cancellation test layout (PYPOST-1265)

PYPOST-1265 changes tests only; production code is unchanged. Each
`CollectionImportParseWorker.run()` checkpoint described in
[Cooperative cancellation](#cooperative-cancellation-pypost-1229) has a test that fails when the
checkpoint is removed. The test doubles (`_GatedWorker`, `_HeldReader`, `_RecordingReader`,
`_OutcomeRecorder`, `_release_on_interrupt`, `_stop_worker`) are local to
`tests/test_collection_import_cancellation_repro.py`.

- **Pre-start (pre-read check)**:
  - `test_worker_pre_start_interruption_skips_reader`
  - `test_teardown_pre_start_interruption_applies_nothing`
- **Record checkpoint, real parser** (in `tests/test_collection_import_reader_contract.py`):
  - `test_production_json_reader_contract[None|1|2]`
  - `test_production_yaml_reader_contract[None|1|2]`
- **Record checkpoint, in flight**:
  - `test_worker_stops_promptly_when_interrupted_mid_parse`
  - `test_teardown_worker_stops_after_interruption` (explicit 1000 ms budget)
  - `test_default_teardown_requests_interruption_before_wait_and_discards_result`
    (default 5000 ms budget)
- **Post-read final guard** (unchanged):
  - `test_final_publication_guard_discards_result_after_last_checkpoint`

All tests except the two contract tests are in
`tests/test_collection_import_cancellation_repro.py`.

#### Pre-start interruption: why `_GatedWorker`

Qt ignores `QThread.requestInterruption()` while the thread is not running, so a request made
before `start()` never reaches `run()`. The production pre-read check can only fire in the short
window after `start()` and before `run()` reaches that check (for example, an immediate teardown
after `_start_parse()`). `_GatedWorker` subclasses `CollectionImportParseWorker` and holds that
window open: its `run()` sets `entered`, waits on the bounded `release` event, and then calls the
unmodified `super().run()`. The test calls `requestInterruption()` while the real thread is held,
then releases it. The predicate is never patched and no production line is skipped.

Rejected alternatives: calling `run()` synchronously (the flag is `False` off-thread, so the test
would have to mock `isInterruptionRequested()`), and a barrier inside the reader (the reader runs
after the pre-read check, so the `(0, 0)` decode checkpoint would catch the request instead).

The proof is that `_RecordingReader.calls == []`: the reader was never called. The tests also
check no progress, `cancelled == [True]`, no completion and no failure. The teardown variant
patches `CollectionImportParseWorker` in `pypost.ui.presenters.collection_import_actions` with
`_GatedWorker` and calls `teardown(timeout_ms=1000)`. It then asserts that `refresh_tree`,
`restore_tree_state`, `emit_collections_changed` and the result dialog were not called, that
`FakeRequestManager.collections == []`, that the worker was reaped and that the action is idle.

#### Record-level cancellation with the real parser

`test_production_json_reader_contract` (PYPOST-1266) and `test_production_yaml_reader_contract`
run `load_collection_import_candidates` on a real file in `tmp_path`. The file holds three
records: `c1/First`, an invalid record with no `name`, and `c3/Third`. For `cancel_at=k` the
progress is exactly `[(1, 3) .. (k, 3)]`, with one cancellation and no completion. For `None`
the parse completes with `c1` and `c3` and one error that mentions `name`. A `(k, 3)` checkpoint
exists only after decoding produced the records, so these tests prove the record checkpoint, not
the decode checkpoint. Decode cancellation on large files is covered by
`tests/test_collection_import_decode_cancellation.py` (see
[Preparation checkpoints](#preparation-checkpoints-pypost-1267)).

#### In-flight proof without wall-clock thresholds

The three in-flight tests use `_HeldReader(hold_at=1)`, a 40-record reader. After checkpoint 1
returns, it sets `holding` and waits on `release`, so it cannot finish while held. The worker
test calls `requestInterruption()` and then sets `release`. The teardown tests wrap the worker's
`requestInterruption` with `_release_on_interrupt`, which sets `release` only after the real
request, so the worker always sees the flag when it resumes. Each test asserts:

- `processed == [1, 2]` and `processed[-1] < total`: the worker stopped at the next checkpoint;
- `observed == ["CollectionImportCancelled"]`: the reader saw the cancellation exception;
- `hold_timed_out` is `False`.

This replaces the PYPOST-1229 sleep-based reader (40 records, 50 ms each) and its 300 ms
wall-clock check, which depended on runner speed. The explicit-budget test keeps
`_TEARDOWN_WAIT_IDLE_MS = 1000`; after the release the budget only has to cover one checkpoint
and thread exit. The default-budget test asserts the 5000 ms deadline by patching the private
`_wait_idle_until` ([PYPOST-1327](https://pypost.atlassian.net/browse/PYPOST-1327)).

#### Exact outcome counts

`_OutcomeRecorder` connects `parse_progress`, `parse_cancelled`, `parse_completed` and
`parse_failed` with `Qt.ConnectionType.DirectConnection`. It counts emissions on the worker
thread, whether or not queued delivery happens later. Every cancellation test asserts
`cancelled == [True]`, `completed == []` and `failed == []`. The explicit-budget teardown test
also patches `show_collection_import_result`, so a regression that publishes a result fails
instead of blocking on a dialog.

#### Bounds and cleanup

Both modules set `pytestmark = pytest.mark.timeout(30)`. Every gate and hold wait is
`Event.wait(timeout=_GATE_S)` with `_GATE_S = 5.0`, and worker joins use
`wait(_WORKER_WAIT_MS)` (5000 ms). On a timeout the double records `gate_timed_out` or
`hold_timed_out`, which the test asserts is `False`, so a lost release fails instead of hanging.
`finally` sets the release event first and then calls `_stop_worker`. No new `process_until`
call is added ([PYPOST-1320](https://pypost.atlassian.net/browse/PYPOST-1320)).

#### Running the tests

```bash
make test WORKERS=1 PYTEST_ARGS='tests/test_collection_import_cancellation_repro.py \
  tests/test_collection_import_reader_contract.py'
```

The run collects 25 tests (6 in the repro module, 19 in the contract module) and takes about
3 s.

#### Mutation-red validation

Production did not change, so there was no natural red. Instead, each mutation below was applied
alone to production code in a throwaway worktree, with the new tests copied in, and reverted
afterwards. Each one turned the named tests red with assertion failures:

- **M1**: delete the pre-read `isInterruptionRequested()` check in `run()`. Both pre-start tests
  fail (`reader calls` is not empty). No older test noticed.
- **M2**: swallow record `on_progress` exceptions for `.yaml`/`.yml` in
  `load_collection_import_candidates`. YAML `[1]` and `[2]` fail. JSON and YAML `[None]` stay
  green, so this proves YAML-specific coverage.
- **M3**: emit `parse_cancelled` twice. All five new or changed worker and teardown tests fail
  on `cancelled == [True]`. The old PYPOST-1229 versions passed.
- **M4**: `_emit_progress` ignores interruption for `done > 0`. The three in-flight tests fail
  with `processed=[1..40]`. The old default-teardown test passed, and the old worker test failed
  only through its 300 ms wall clock.

Repeat this check when changing these tests: a mutation that keeps a test green means that test
no longer proves its checkpoint. The full table is in the PYPOST-1265 roadmap, STEP 3
(`ai-tasks/PYPOST-1265/00-roadmap.md`).

#### Log events on these paths

No log events were added. The paths emit existing events (see [Observability](#observability)):

- Worker: INFO `collection_import_parse_worker_cancelled path=…`. One handler serves the
  pre-read, record and post-read checkpoints, so the line does not say which one fired.
- Presenter: INFO `collection_import_parse_cancelled from_state=…`, and the teardown events
  `collection_import_teardown_started`, WARNING `collection_import_worker_interrupting`,
  `collection_import_wait_idle_*`, INFO `collection_import_worker_interrupted`, WARNING
  `collection_import_worker_interrupt_timeout` and DEBUG `collection_import_worker_reaped`.

Only two tests assert logs. `test_worker_pre_start_interruption_skips_reader` expects exactly one
`collection_import_parse_worker_cancelled` record. `test_teardown_worker_stops_after_interruption`
expects `collection_import_worker_interrupted`, exactly one
`collection_import_parse_cancelled from_state=parsing` and no
`collection_import_worker_interrupt_timeout`. The other tests check behaviour only; behaviour is
the primary proof.

#### Follow-ups

From [PYPOST-1265 technical debt](../../ai-tasks/PYPOST-1265/60-tech-debt.md):

- **[PYPOST-1328](https://pypost.atlassian.net/browse/PYPOST-1328)** (Low) — add
  `stage=pre_read|record|post_read` (plus `done`/`total`) to the worker cancellation log.
- **[PYPOST-1329](https://pypost.atlassian.net/browse/PYPOST-1329)** (Low) — record a distinct
  metric outcome for cancellation instead of `rejected`, which file-picker dismissal also uses.
- **[PYPOST-1330](https://pypost.atlassian.net/browse/PYPOST-1330)** (Low) — move
  `_OutcomeRecorder` (and optionally `_stop_worker`) into a shared `tests/helpers/` module.
- **[PYPOST-1331](https://pypost.atlassian.net/browse/PYPOST-1331)** (Lowest) — move the
  final-guard test to `_stop_worker` and bounded `Event.wait` waits.

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
- **`CollectionImportActions.wait_idle(timeout_ms=None)`** (policy default 5000 ms) pumps the
  `QApplication` event loop in a bounded loop until `is_busy()` returns `False`. It may deliver
  queued worker-finish and deferred-cleanup handlers, but it is not an explicit native-thread
  join on the `QApplication` path.
- **`CollectionsPresenter.wait_import_idle(timeout_ms=None)`** exposes this wait condition on the
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
  - **Wait**: Runs the `wait_idle()` loop on the shared teardown deadline (PYPOST-1264) to
    process events while active workers cancel or finish until `is_busy()` reports `False`. It
    does not explicitly join or reap on the `QApplication` path.
  - **Disconnect**: Safely disconnects all Qt signals (`parse_progress`, `parse_completed`,
    `parse_failed`, `parse_cancelled`, `finished`) within `try...except (RuntimeError, TypeError)`
    blocks.
  - **Join**: If the worker thread remains running, requests interruption again and waits
    `min(final_join_ms, remaining)` for clean exit (PYPOST-1264; originally a fixed 100 ms).
    This final join can time out.
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

### Planner CPU-work benchmark (PYPOST-1263)

`tests/test_collection_import_profile.py::test_plan_collection_import_large_dataset_performance`
plans 500 incoming collections (2,500 requests, 25 conflicts covering all three decision types)
against 50 existing ones. The fixture and conflict discovery run before the timed interval.

- **What it measures**: current-thread CPU time (`time.thread_time()`) around the single
  `plan_collection_import` call. The gate is strict: `cpu_ms < 100.0`. Wall time
  (`time.perf_counter()`) is measured around the same call, but only appears in the failure
  message.
- **What it does not measure**: user-visible UI wall latency. The test is a CPU-work budget for
  the planner. It does not guarantee a 100ms response on a loaded host.
- **Why**: the earlier wall-clock gate failed intermittently under parallel full-suite load. The
  same run passed at about 49ms in isolation. Descheduling and contention from other workers
  were counted as planner time. Thread CPU time leaves out time the thread is not running and
  work done by other threads. The budget was not raised, and no retries or skips were added.
- **Assumption**: the planner is synchronous and in-memory. If it starts handing work to another
  thread or doing blocking I/O, `thread_time()` will under-count that work and the gate must be
  revisited.

A failure looks like this:

```text
plan_collection_import used 132.40ms thread CPU, exceeding 100ms CPU budget (wall elapsed: 140.12ms)
```

Read it as follows:

- High CPU with wall close to CPU means the planner does more work than before. Treat it as a
  real regression and profile the planner.
- High CPU with much higher wall time still means a CPU regression. The extra wall time is
  scheduling delay on top of it.
- High wall time alone never fails this test. If a wall-time assertion fails in this module, it
  is one of the remaining wall-gated tests listed below.

Deterministic regressions for the gating policy live in
`tests/test_collection_import_profile_clock.py`
(`test_planner_benchmark_distinguishes_cpu_work_from_wall_delay`). They replace the profile
module's `time` binding with fake clocks and wrap the real planner in a spy. Four cases are
covered: `external-descheduling` (20ms CPU, 500ms wall passes), `excess-planner-work` and
`strict-cpu-boundary` (150ms and exactly 100ms CPU fail), and `synthetic-low-wall-high-cpu`
(150ms CPU fails even with 10ms wall). They also check that both clocks are read exactly twice,
after fixture setup and around the one planner call. Because they patch the module-level `time`,
`plan_collection_import`, `_make_sample_collections`, and `find_collection_conflicts` names,
renaming those or switching the benchmark to `from time import ...` makes these tests fail.

Run both modules through Make:

```bash
make test WORKERS=1 PYTEST_ARGS='tests/test_collection_import_profile.py tests/test_collection_import_profile_clock.py'
```

Remaining wall-clock gates (not changed by PYPOST-1263):

- **[PYPOST-1318](https://pypost.atlassian.net/browse/PYPOST-1318)**:
  `test_plan_collection_import_conflict_matrix_profile` (50ms wall) and
  `test_apply_imported_collections_performance` (500ms wall) in the same module can still flake
  under contention.
- **[PYPOST-1317](https://pypost.atlassian.net/browse/PYPOST-1317)**: Qt event-loop latency
  thresholds in `tests/test_pypost_1242_failing_repro.py` and
  `tests/test_websocket_echo_server.py`. Wall latency is the real metric there, so they need
  their own design rather than a switch to CPU time.

## Configuration

There is no new application setting, environment variable, on-disk format,
`StorageInterface` method, or third-party dependency. The file-dialog filter, caption, and
preparing status text are constants in `collection_messages.py`.
PYPOST-1266 changes the injected reader contract through types and direct invocation; there is no
compatibility flag to restore readers that omit the checkpoint keyword.
PYPOST-1267's 64 Ki-character read size and 4096-unit scan/lookahead/assembly windows are internal
bounded-work constants, not configurable file limits. There is no setting to enable checkpoints;
supplying the callback selects cooperative preparation automatically.

The lifecycle methods expose bounded waits for callers that need a different test or teardown
budget. Their limits come from `CollectionImportLifecyclePolicy` (PYPOST-1264); they are fixed
policy values, not a user setting or environment variable (see
[Measured latency and configurability decision](#measured-latency-and-configurability-decision)):

- `CollectionImportActions.wait_idle(timeout_ms=None)` pumps the Qt event loop while waiting for
  the action to report `IDLE`; `None` means `teardown_budget_ms` (5000 ms). Queued cleanup may
  clear the worker reference, but this method does not explicitly join the worker on the
  `QApplication` path.
- `CollectionImportActions.teardown(timeout_ms=None)` requests interruption before waiting. All
  of its waits share one deadline: if a worker is still running after the idle wait, the final
  join gets `min(final_join_ms, remaining)` (100 ms at most) and the library join gets the rest.
  `worker_finish_join_ms` (100 ms) is the join on the normal `finished` path and is not capped.
- Code that needs other limits passes a `CollectionImportLifecyclePolicy` as the keyword-only
  `lifecycle_policy` constructor argument of `CollectionImportActions`.

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
`ai-tasks/PYPOST-1182/50-observability.md`,
`ai-tasks/PYPOST-1148/50-observability.md`, and
`ai-tasks/PYPOST-1264/50-observability.md`.

### Async parse, lifecycle synchronization, and teardown (PYPOST-1005 / PYPOST-1182 / PYPOST-1148 /
PYPOST-1229 / PYPOST-1264)

In `collections_presenter.py`:

- **INFO** `collections_presenter_teardown_started timeout_ms=%d` — start of presenter-level
  teardown sequence (PYPOST-1148); `timeout_ms` is the resolved budget, so a `None` argument
  logs the policy default 5000 (PYPOST-1264)
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
  its timeout before the action became idle (PYPOST-1182). Inside teardown, `elapsed_ms` is
  counted from the start of teardown (shared deadline, PYPOST-1264)
- **INFO** `collection_import_teardown_started timeout_ms=%d` — start of actions teardown
  (PYPOST-1148); `timeout_ms` is the resolved budget of the shared deadline
- **INFO** `collection_import_teardown_completed clean=%s elapsed_ms=%d timeout_ms=%d` —
  completion of actions teardown (PYPOST-1148). `elapsed_ms` is the total teardown time and
  `timeout_ms` the budget, so an overrun can be read from this one line (PYPOST-1264)
- **WARNING** `collection_import_worker_interrupting` — worker active when teardown started;
  interruption requested (PYPOST-1148)
- **WARNING** `collection_import_worker_interrupt_timeout wait_ms=%d elapsed_ms=%d` — the
  final file-worker join timed out (PYPOST-1148). `wait_ms` is the join it actually got,
  `min(final_join_ms, remaining)`; `elapsed_ms` is time since teardown started (PYPOST-1264)
- **INFO** `collection_import_worker_interrupted` — running worker stopped successfully after
  interruption (PYPOST-1148)
- **INFO** `collection_import_parse_cancelled from_state=…` — the GUI received the dedicated
  cancellation signal and returned the presenter to `IDLE` without applying results (PYPOST-1229)
- **DEBUG** `collection_import_worker_reaped` — worker reference reaped and scheduled for
  deletion (PYPOST-1148)
- **ERROR** `collection_import_parse_unexpected error=…` — unexpected exception from the
  worker, handled on the GUI thread (invalid-file dialog)
- **WARNING** `collection_import_worker_finish_wait_timeout wait_ms=…` — short join after
  `QThread.finished` did not complete; `wait_ms` is `worker_finish_join_ms` (100), which is not
  on the teardown deadline
- **WARNING** `collection_library_import_worker_timeout wait_ms=%d elapsed_ms=%d` — the
  library-worker join in teardown timed out. `wait_ms` is the remaining budget it got;
  `elapsed_ms` is time since teardown started (PYPOST-1264)

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

Reading the teardown timeout fields (PYPOST-1264):

- `wait_ms=0` on `collection_import_worker_interrupt_timeout` or
  `collection_library_import_worker_timeout` means the budget was already used up before that
  join, so the worker only got a `wait(0)` probe. Look for an earlier phase that used it,
  usually `collection_import_wait_idle_timeout`. The worker itself may not be stuck.
- `wait_ms>0` means the worker got that much time and still did not stop: a reader blocked
  outside its checkpoints, or a library operation (which cannot be interrupted).
- On `collection_import_teardown_completed`, `elapsed_ms` above `timeout_ms + 50`
  (`budget_tolerance_ms`) means time was spent outside the bounded waits. See "Teardown takes
  longer than its budget" in the Troubleshooting section below.

Examples (messages only; the first is the exact output of the fake-clock test
`test_teardown_timeout_logs_report_phase_waits_and_elapsed`, the second has illustrative
timings). Both workers stuck, policy budget 200 ms and `final_join_ms=30`:

```text
INFO    collection_import_teardown_started timeout_ms=200
WARNING collection_import_worker_interrupting
WARNING collection_import_worker_interrupt_timeout wait_ms=30 elapsed_ms=30
WARNING collection_library_import_worker_timeout wait_ms=170 elapsed_ms=200
INFO    collection_import_teardown_completed clean=False elapsed_ms=200 timeout_ms=200
```

Budget of 100 ms used up in the idle wait, so both joins only probe (excerpt):

```text
WARNING collection_import_wait_idle_timeout elapsed_ms=100
WARNING collection_import_worker_interrupting
WARNING collection_import_worker_interrupt_timeout wait_ms=0 elapsed_ms=100
WARNING collection_library_import_worker_timeout wait_ms=0 elapsed_ms=101
INFO    collection_import_teardown_completed clean=False elapsed_ms=101 timeout_ms=100
```

Malformed, unreadable, or wrong-shaped file failures (`CollectionImportFileError`) are logged
twice on purpose: worker WARNING confirms the off-thread failure, and the orchestrator then
emits the terminal `collection_import_file_invalid` “nothing changed” event used since
PYPOST-987. A parse that returns no valid collections also emits that event with
`reason=no_valid_collections`.

Unexpected reader exceptions follow a different path: the worker logs
`collection_import_parse_worker_failed` at ERROR level, and the orchestrator logs
`collection_import_parse_unexpected` at ERROR level before showing the invalid-file dialog.
They do not emit `collection_import_file_invalid`. Unsupported single-argument readers take this
path with `TypeError`; no additional logging or metrics configuration is required by PYPOST-1266.

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
  - Cause: The short post-`finished` join did not complete within the policy
    `worker_finish_join_ms` (100 ms). This join is not on the teardown deadline, so when it
    runs during teardown it can push `elapsed_ms` past the budget (design Risk 3,
    [PYPOST-1322](https://pypost.atlassian.net/browse/PYPOST-1322)).
  - Fix: This is the same class of issue as storage gateway finish hygiene (PYPOST-829).
    It is usually transient; escalate if paired with crashes under rapid import churn.

- **WARNING `collection_import_wait_idle_timeout`**
  - Cause: `wait_idle()` reached its timeout before the import action reported `IDLE`.
    A slow reader or queued worker cleanup may be responsible.
  - Fix: Check whether `read_import_file` is blocked on slow I/O or a deadlocked event
    loop. Use `teardown()` when interruption and a bounded final worker wait are needed;
    increase `timeout_ms` for legitimate massive-file parses. Inside teardown this line means
    the idle wait used the whole shared budget; the following join timeouts then show
    `wait_ms=0`.

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

- **Custom reader fails with an unexpected `on_progress` keyword**
  - Cause: The reader does not implement `ReadImportFile`. Single-argument readers are no longer
    accepted by the background worker; argument binding raises `TypeError` and emits `parse_failed`.
  - Fix: Add the `on_progress` keyword to the reader or forward it through a compatible wrapper.
    Invoke it at safe record boundaries and let its exceptions propagate immediately. An optional
    callback default is allowed, but the worker always supplies the callback. Do not discard it
    in a wrapper or retry without it.

- **Panel close does not cancel promptly**
  - Cause: A custom reader omits preparation checkpoints, a native/storage operation stalls,
    or one record's model validation is expensive.
  - Fix: Treat cancellation as cooperative. A custom reader that never invokes its supplied
    callback violates the contract; restore its safe record checkpoints and exception propagation.
    Keep per-record work bounded. The production reader now checks active loading/decoding;
    run the focused preparation regressions above to isolate a regression from environmental
    stalls or custom reader behavior. Increasing a teardown budget does not add checkpoints.

- **Direct callback reports zero totals or cancellation becomes a parse error**
  - Cause: A consumer treats `(0, 0)` as record progress, or a wrapper catches checkpoint
    exceptions inside a broad file/parser error handler.
  - Fix: Consume `(0, 0)` as a preparation checkpoint, suppress record percentage updates,
    and propagate callback exceptions. Use the public reader's origin-protection boundary;
    preserve YAML fallback's original JSON error only for ordinary decoding failures.

- **`parse_completed` appears after cancellation was requested**
  - Cause: `parse_completed` may already have been published before interruption was requested,
    or interruption can arrive in the small residual window after the final guard and before
    `parse_completed.emit()`. Supported readers all receive the checkpoint, and the final guard
    also checks interruption after the reader returns. That guard does not make the check and
    publication atomic.
  - Fix: Check the worker and presenter cancellation logs. The final post-reader guard narrows
    but does not eliminate the publication race; interruption can still arrive between that
    check and `parse_completed.emit()`. The typed contract does not remove that residual race,
    and cancellation does not roll back work already in `APPLYING`.

- **WARNING `collection_import_worker_interrupt_timeout`**
  - Cause: The worker failed to stop within its final join, `min(final_join_ms, remaining)`
    (100 ms at most). With `wait_ms=0` the budget was already used up and the join was only a
    probe.
  - Fix: With `wait_ms>0`, check whether the custom reader is blocked in uninterruptible I/O or
    decoding, or in a long single-record operation. With `wait_ms=0`, look at the earlier
    phase that used the budget first (usually `collection_import_wait_idle_timeout`). No
    forcible termination fallback exists (PYPOST-1229).

- **WARNING `collection_library_import_worker_timeout`**
  - Cause: A connected-library import or refresh was still running when teardown gave it the
    remaining budget (`wait_ms`). The library worker cannot be interrupted, so it always uses
    all of the remaining budget and is then released while still running
    ([PYPOST-1324](https://pypost.atlassian.net/browse/PYPOST-1324)).
  - Fix: With `wait_ms=0`, an earlier phase used the budget. With `wait_ms>0`, check what the
    library operation is blocked on. Pass a larger `timeout_ms` only if the caller
    can afford it.

- **Teardown takes longer than its budget**
  - Cause: Find `collection_import_teardown_completed clean=… elapsed_ms=… timeout_ms=…`. If
    `elapsed_ms` is within `timeout_ms + 50` (`budget_tolerance_ms`), teardown met its contract.
    If it is larger, time went to work outside the bounded waits: the nested worker-finish join
    (look for `collection_import_worker_finish_wait_timeout` in the same span), a long queued
    GUI slot run by `processEvents()` (for example an apply), or slow logging handlers.
  - Fix: Read the `wait_ms` / `elapsed_ms` of each timeout line in order to see which phase used
    the budget (see the [Observability](#observability) reading guide). In tests run under
    `make test`, pytest live logging can cost hundreds of ms per WARNING record
    ([PYPOST-1326](https://pypost.atlassian.net/browse/PYPOST-1326)); confirm with
    `PYTEST_ARGS="... -o log_cli=false"` before treating it as a product regression. If the
    whole app hangs on close during an import, note that application shutdown does not call
    collection import teardown yet ([PYPOST-1321](https://pypost.atlassian.net/browse/PYPOST-1321)).

- **`test_plan_collection_import_large_dataset_performance` fails with "thread CPU, exceeding
  100ms CPU budget"**
  - Cause: The planner used at least 100ms of current-thread CPU. Host contention alone does
    not cause this failure; it adds wall time, not thread CPU.
  - Fix: Treat it as a planner work regression and profile `plan_collection_import`. Use the
    wall value in the message only as context. See
    [Planner CPU-work benchmark](#planner-cpu-work-benchmark-pypost-1263).

### Known follow-ups

The reader-dependent guarantee gap from
[PYPOST-1229 technical debt](../../ai-tasks/PYPOST-1229/60-tech-debt.md) is resolved by
PYPOST-1266's typed protocol, direct invocation, migrated fakes, and focused contract tests.
Remaining cancellation and lifecycle work is recorded in
[PYPOST-1266 technical debt](../../ai-tasks/PYPOST-1266/60-tech-debt.md):

- **[PYPOST-1264](https://pypost.atlassian.net/browse/PYPOST-1264)** — done: see
  [Teardown lifecycle policy](#teardown-lifecycle-policy-pypost-1264). Its own follow-ups are
  listed below.
- **[PYPOST-1265](https://pypost.atlassian.net/browse/PYPOST-1265)** — done: see
  [Cancellation test layout](#cancellation-test-layout-pypost-1265) (pre-start interruption,
  real YAML record checkpoint, exact outcome counts, in-flight proof). Its follow-ups
  PYPOST-1328..1331 are listed in that section.
- **[PYPOST-1261](https://pypost.atlassian.net/browse/PYPOST-1261)** — pre-existing malformed
  nested-expression, frozen SOLID snapshot, and process-level Qt baseline failures.
- **[PYPOST-1262](https://pypost.atlassian.net/browse/PYPOST-1262)** — pre-existing,
  load-sensitive nested-Make timeout failures.

Follow-ups from [PYPOST-1264 technical debt](../../ai-tasks/PYPOST-1264/60-tech-debt.md):

- **[PYPOST-1321](https://pypost.atlassian.net/browse/PYPOST-1321)** (High) — register
  collection import teardown with main-window shutdown; today app close during an import does
  not interrupt or join its workers under any budget.
- **[PYPOST-1322](https://pypost.atlassian.net/browse/PYPOST-1322)** (Lowest) — test the
  uncapped nested worker-finish join during teardown (Risk 3).
- **[PYPOST-1323](https://pypost.atlassian.net/browse/PYPOST-1323)** (Low) — move the other
  `_WORKER_FINISH_WAIT_MS = 100` constants behind named lifecycle policies.
- **[PYPOST-1324](https://pypost.atlassian.net/browse/PYPOST-1324)** (Medium) — make
  `LibraryOperationWorker` interruptible so teardown does not use the whole remaining budget.
- **[PYPOST-1325](https://pypost.atlassian.net/browse/PYPOST-1325)** (Low) — name the
  application shutdown budget (the main-window 5000 ms literals) and its per-owner allocation.
- **[PYPOST-1326](https://pypost.atlassian.net/browse/PYPOST-1326)** (Medium) — make `make test`
  live logging cheap or off for parallel runs, then remove the guard's logger-disable
  workaround.
- **[PYPOST-1327](https://pypost.atlassian.net/browse/PYPOST-1327)** (Low) — public teardown
  observation seam instead of patching `_wait_idle_until`; decide whether `budget_tolerance_ms`
  is checked anywhere.

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

PYPOST-1264 runs also saw these filed, pre-existing failures (all reproduced or known at base
`c3f8e183`):

- **PYPOST-1299** — `tests/test_pytest_exit_policy.py` times out at 120 s.
- **PYPOST-1311** — `tests/test_env_persistence_e2e.py` tmp cleanup `OSError: Directory not
  empty`.
- **PYPOST-1315** — `tests/test_environment_export_ui.py` process exits -11/-7 after its tests
  pass.
- **PYPOST-1320** — intermittent hang in
  `tests/test_collection_import_teardown_repro.py` and `tests/test_collections_import_ui.py`:
  the main thread blocks starting the `process_until` watchdog `threading.Timer`, before any
  teardown code runs.

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
