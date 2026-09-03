# PYPOST-1228: Refactor CollectionImportActions internal state flags into CollectionImportState enum

## Research

Current state tracking in `pypost/ui/presenters/collection_import_actions.py`:

- `self._worker: CollectionImportParseWorker | None = None` and `self._preparing = False` are set
  in `__init__` (lines 81-82).
- `is_busy()` (line 84-86): `return self._preparing or self._worker is not None`.
- `_set_preparing(active)` (line 262-281) is the single place `_preparing` is written. It also
  toggles the import button's enabled state and shows/clears the busy-cue status message
  (`MSG_IMPORT_PREPARING` / clear), and logs `collection_import_busy_cue_shown` /
  `_cleared`. This method is the de-facto "busy cue" side-effect hook, not just a flag setter.
- Call sites of `_set_preparing`:
  - `_start_parse()` line 172: `_set_preparing(True)` right before constructing and starting the
    `CollectionImportParseWorker` (QThread).
  - `_on_parse_completed()` line 191: `_set_preparing(False)` as the **first** statement, before
    branching into either the "no valid collections" error path or `_finish_import()`
    (conflict resolution → planning → `apply_imported_collections` → refresh/restore/emit).
  - `_on_parse_failed()` line 202: `_set_preparing(False)` as the first statement.
  - `teardown()` line 152: `_set_preparing(False)` unconditionally near the end, after the worker
    (if any) has been disconnected/interrupted/reaped.
- `self._worker` is written in three places:
  - `_start_parse()` line 178: set to the newly created worker, right before `worker.start()`.
  - `_on_worker_finished()` line 210-212: `finished = self._worker; self._worker = None` — this
    runs on the worker's Qt `finished` signal, connected in `_start_parse()` line 177
    (`worker.finished.connect(self._on_worker_finished)`). Per the module's Qt threading model,
    `finished` fires asynchronously on the GUI thread sometime after the worker's run loop
    returns — its *timing relative to* `parse_completed`/`parse_failed` is not fixed by Qt
    signal-ordering guarantees the way same-object signal emission order is; both are separate
    signals emitted from the worker thread and queued to the GUI thread. This is exactly the
    mechanism the requirements' "Problem" section describes: `_worker` can already be cleared
    (by `_on_worker_finished`) by the time `_finish_import()` (invoked synchronously from
    `_on_parse_completed`) runs, or vice versa — either ordering is possible, which is why two
    independent flags were needed in the first place and why they can now disagree.
  - `teardown()` line 151: set to `None` after interrupting/joining/reaping the worker.
- **The gap**: `_on_parse_completed()` clears `_preparing` (making that half of `is_busy()`
  false) *before* calling `_finish_import()` synchronously. `_finish_import()` runs entirely on
  the GUI thread (conflict dialogs via `_resolve_conflicts()`, `plan_collection_import()`,
  `apply_imported_collections()`, tree refresh, `emit_collections_changed()`) and can take a
  visible amount of time (modal dialogs). If `_on_worker_finished()` has *already* fired for this
  worker by the time `_on_parse_completed` runs (both are queued signals from the same worker;
  nothing enforces `finished` always arriving after `parse_completed` is fully handled), `_worker`
  is already `None`, so `is_busy()` returns `False` for the entire `_finish_import()` window —
  confirmed by the requirements doc and independently derivable from the code: neither
  `_on_parse_completed` nor `_finish_import` touches `_worker`, and `_worker` is otherwise only
  cleared by `_on_worker_finished`.
- `wait_idle()` and `teardown()` both key off `is_busy()` as their loop condition / gate, so
  whatever `is_busy()` is redefined to mean, both continue to work unchanged as long as the new
  definition stays true for the same (or a superset of the same) real-world windows.
- `import_collections()` (line 159-169) is the only re-entrancy guard call site: `if
  self.is_busy(): return` before prompting the file picker. This is the guard the "re-entrant
  trigger" user scenarios (2-4) exercise.
- Precedent for where small Qt-free enums live in this codebase: `pypost/core/import_conflicts.py`
  defines `ImportConflictDecision(str, Enum)` as a standalone Qt-free module already imported by
  this same presenter (`from pypost.core.import_conflicts import ImportConflictDecision`, line
  34). `pypost/core/collection_import.py` is the Qt-free module the presenter's docstring
  describes as owning "all decision logic," with `CollectionImportActions` reduced to "only
  sequences it against dialogs and app state" (module docstring, lines 3-9).

## Implementation Plan

1. Add a `CollectionImportState` enum with members `IDLE`, `PREPARING`, `PARSING`, `APPLYING` to
   a new Qt-free module `pypost/core/collection_import_state.py`, following the
   `ImportConflictDecision(str, Enum)` precedent in `pypost/core/import_conflicts.py` (string enum
   for readable logging/repr and easy test assertions, e.g.
   `presenter._state is CollectionImportState.PARSING` or `presenter._state.value ==
   "parsing"`).
2. In `CollectionImportActions.__init__`, replace `self._worker` and `self._preparing` with:
   - `self._worker: CollectionImportParseWorker | None = None` (kept — it is still needed to hold
     the actual worker reference for `teardown()`/`wait_idle()` mechanics; it is no longer part of
     the busy computation).
   - `self._state: CollectionImportState = CollectionImportState.IDLE`.
3. Redefine `is_busy()` as `return self._state is not CollectionImportState.IDLE`. This makes
   `_state` the single authoritative source `is_busy()` reads, per the requirements' Definition of
   Done.
4. Introduce one private transition helper, `_set_state(self, state: CollectionImportState) ->
   None`, replacing `_set_preparing(active: bool)`. It performs the same side effects
   `_set_preparing` does today (button enable/disable, busy-cue show/clear, debug log), driven by
   whether the target state is `IDLE` or not, so the observable button/status-message behavior is
   byte-for-byte unchanged:
   - `active = state is not CollectionImportState.IDLE` computed once, used exactly as
     `_set_preparing`'s `active` parameter is used today for the button/status/log branches.
   - Sets `self._state = state` before running the side effects (ordering does not matter here
     since nothing re-enters synchronously from within the button/status/log calls).
5. Rewire every current `_set_preparing` call site to pass the concrete state for that point in
   the flow, keeping call sites and control flow otherwise identical:
   - `_start_parse()`: `self._set_preparing(True)` → `self._set_state(CollectionImportState.PREPARING)`,
     still called immediately before constructing/starting the worker (line ~172).
   - Immediately after `worker.start()` returns control flow to `_start_parse`, no change needed —
     parsing progress arrives via `_on_parse_progress`, which does not currently touch
     `_preparing`/`_worker` and will not touch `_state` either (it stays PREPARING→PARSING
     transition point is described next).
   - **New**: transition to `PARSING` when the worker actually starts running, i.e. right after
     `worker.start()` in `_start_parse()` (this is the natural boundary between "we've kicked off
     the background parse" and "worker is executing" — `QThread.start()` returns immediately once
     the thread is scheduled, so setting `PARSING` right after `start()` keeps `is_busy()` true
     across the whole PREPARING→PARSING boundary with no gap). Concretely:
     `worker.start(); self._set_state(CollectionImportState.PARSING)` at the end of
     `_start_parse()`. (Requirements' four named stages list PREPARING as "worker not yet started
     / picking up" and PARSING as "background parse worker running" — this placement matches that
     wording exactly: PREPARING covers file-chosen-to-worker-construction, PARSING starts once
     `start()` has been issued.)
   - `_on_parse_completed()`: currently `self._set_preparing(False)` as the first line, then
     branches. Replace with the **gap-closing** transition:
     - If `not collections` (no valid collections → error path, no `_finish_import` call): call
       `self._set_state(CollectionImportState.IDLE)` (equivalent of today's
       `_set_preparing(False)`), then show the error dialog. This preserves scenario 5 (invalid
       file/parse failure never enters APPLYING).
     - Otherwise (valid collections → about to call `_finish_import`): call
       `self._set_state(CollectionImportState.APPLYING)` **instead of** clearing to IDLE, then call
       `self._finish_import(collections, parse_errors)` as today. This is the core fix: `_state`
       is APPLYING for the entire duration of `_finish_import()` (conflict dialogs, planning,
       `apply_imported_collections`, refresh/restore/emit), so `is_busy()` reports `True`
       throughout — closing the exact gap the requirements identify, independent of whatever
       `_worker`/`_on_worker_finished` timing race exists, since `_worker` no longer participates
       in `is_busy()` at all.
     - At the **end** of `_finish_import()` (after `show_collection_import_result(...)`, its last
       statement today), add `self._set_state(CollectionImportState.IDLE)` as the final statement,
       returning the module to IDLE once the whole applying phase (including the result dialog)
       has completed. This is the transition "back to IDLE after `_finish_import()`" the task
       asks for.
   - `_on_parse_failed()`: `self._set_preparing(False)` → `self._set_state(CollectionImportState.IDLE)`,
     unchanged position (first line), preserving scenario 5 for the failure-signal path.
   - `teardown()`: `self._set_preparing(False)` → `self._set_state(CollectionImportState.IDLE)`,
     unchanged position (after worker disconnect/interrupt/reap, unconditional). This still forces
     IDLE regardless of which state teardown was called from (PREPARING, PARSING, or now also
     APPLYING), satisfying user scenario 6. Note `_finish_import()` itself is synchronous and runs
     to completion on the GUI thread once started — `teardown()` cannot interrupt it mid-flight
     any more than it can today (today's code has the same property: nothing preempts a running
     Python call frame). `teardown()`'s existing contract ("wait for and clean up in-flight work")
     is about the async worker; it is unaffected by the APPLYING-window's now-correct `is_busy()`
     reporting, because `teardown()` never busy-waits on `is_busy()` from *inside*
     `_finish_import()`'s own call stack — that would require re-entrant teardown, which is out of
     scope and unchanged by this refactor.
6. `_on_worker_finished()` keeps its current job (clearing `self._worker` and reaping the QThread)
   entirely unchanged — it becomes purely a resource-lifecycle callback (worker handle + native
   thread join), no longer entangled with busy/idle semantics. This is a deliberate
   separation-of-concerns outcome: "is an import in flight" (`_state`) and "is the worker object
   still alive and needing cleanup" (`_worker`) become two independently-tracked, non-interacting
   facts, removing the race the requirements describe rather than papering over it.
7. No change to `wait_idle()`'s body: it already loops on `is_busy()` / falls back to
   `self._worker.wait(10)` when no `QApplication` instance exists, and `self._worker` is still
   maintained (step 6) for exactly that fallback branch.
8. No change to `import_collections()`'s guard (`if self.is_busy(): return`) — it automatically
   picks up the new, gap-closed `is_busy()` definition.
9. Rename the method `_set_preparing` → `_set_state` throughout (single rename); no other method
   signatures, public API, constructor parameters, or imports used by `CollectionsPresenter`
   change.

**Mandatory — Failing Repro (next Step 3):** A red test asserting the gap-closing behavior:
during `_finish_import()`'s execution (specifically while a conflict-resolution dialog would be
open, or — more simply and deterministically for a unit test — by monkeypatching/stubbing
`apply_imported_collections` or `prompt_collection_import_conflict` to synchronously assert
`presenter.is_busy() is True` from inside the stub before returning), `is_busy()` must report
`True`. Concretely: drive `_on_parse_completed(collections, [])` (or the full
`import_collections()` → simulated `parse_completed` emission path already used by
`tests/test_collections_import_ui.py`'s `_wait_import` helper) with a fake/stub
`request_manager`/conflict-prompt/apply function that captures `presenter.is_busy()` at the point
it is called and stores it for the test to assert on afterward; assert the captured value is
`True`. Against **today's code** this assertion is expected to fail (`is_busy()` is `False` at
that point, per the documented gap) whenever the test's stub runs after the worker's `finished`
signal has already been processed — the existing test suite's `_wait_import` pattern (per
`tests/test_collections_import_ui.py` line 69, `presenter._import_actions.is_busy()`) shows the
tests already drive this presenter through a real/simulated worker lifecycle, so the same harness
can add this assertion. This lives in `tests/test_collections_import_ui.py` alongside existing
import-flow tests, requires no live external dependency (worker is already faked/driven directly
in that suite), and must be written and independently reviewed as a failing (red) test *before*
any of the Implementation Plan changes above are made, then turned green by implementing them.

## Architecture

### Module boundary

- **New module**: `pypost/core/collection_import_state.py` — Qt-free, holds only:
  ```python
  from enum import Enum

  class CollectionImportState(str, Enum):
      IDLE = "idle"
      PREPARING = "preparing"
      PARSING = "parsing"
      APPLYING = "applying"
  ```
  Rationale for a new module rather than adding to `collection_import_state.py`'s nearest
  existing neighbor `pypost/core/import_conflicts.py` or to `collection_import.py`: the enum
  describes the *presenter's* lifecycle (a UI-orchestration concept — "what is
  `CollectionImportActions` doing right now"), not an import-planning decision (which is what
  `collection_import.py` and `import_conflicts.py` own, per the module docstring's explicit
  separation of "decision logic" from "sequencing against dialogs and app state"). A dedicated
  module keeps that boundary clean and gives the enum an unambiguous, greppable home
  (`pypost/core/collection_import_state.py`), consistent with the codebase's existing pattern of
  one small Qt-free module per cohesive concept (`import_conflicts.py`, `tab_dirty.py` as a UI-side
  analogue). It stays in `pypost/core/` (not `pypost/ui/`) because it has zero Qt dependency and
  is a plain value type — nothing prevents it from being reused by a future test helper or another
  presenter without importing Qt.
- `pypost/ui/presenters/collection_import_actions.py` imports it exactly like it imports
  `ImportConflictDecision` today: `from pypost.core.collection_import_state import
  CollectionImportState`.

### State machine

```
        import_collections()                 worker.start()
IDLE ───────────────────────▶ PREPARING ───────────────────────▶ PARSING
  ▲                                                                  │
  │                                                     parse_completed (no valid collections)
  │                                                     or parse_failed
  │◀─────────────────────────────────────────────────────────────────┤
  │                                                                  │
  │                                          parse_completed (valid collections)
  │                                                                  ▼
  │                                                              APPLYING
  │                                                     (_finish_import: conflicts →
  │                                                      plan → apply → refresh/restore/emit)
  │                                                                  │
  └──────────────────────── end of _finish_import() ─────────────────┘

Any state ──── teardown() ────▶ IDLE   (forced, unconditional, after worker
                                          disconnect/interrupt/reap)
```

Transition table:

| From | Event / call site | To | Where in code |
| --- | --- | --- | --- |
| IDLE | `import_collections()` picks a file (not busy) → `_start_parse()` begins | PREPARING | `_start_parse()`, before worker construction |
| PREPARING | `worker.start()` returns | PARSING | end of `_start_parse()` |
| PARSING | `parse_completed` fires, `collections` empty | IDLE | `_on_parse_completed()`, "no valid collections" branch |
| PARSING | `parse_completed` fires, `collections` non-empty | APPLYING | `_on_parse_completed()`, before calling `_finish_import()` |
| PARSING | `parse_failed` fires | IDLE | `_on_parse_failed()`, first line |
| APPLYING | `_finish_import()` reaches its final statement (after result dialog) | IDLE | last line of `_finish_import()` |
| any | `teardown()` called | IDLE | `teardown()`, unconditional, post worker-reap |

`_worker` (the `CollectionImportParseWorker | None` reference) remains a **separate**, orthogonal
piece of state used only for QThread lifecycle mechanics (`wait_idle()`'s no-`QApplication`
fallback, `teardown()`'s disconnect/interrupt/reap sequence, `_on_worker_finished()`'s cleanup). It
is deliberately **not** consulted by `is_busy()` any more — that is precisely what removes the
race, since `_worker`'s clearing (via the async `finished` signal) and `_state`'s APPLYING window
(driven synchronously from `_on_parse_completed`) no longer need to agree with each other for
`is_busy()` to be correct.

### `is_busy()` redefinition

```python
def is_busy(self) -> bool:
    """True while an import is in flight (any stage but idle)."""
    return self._state is not CollectionImportState.IDLE
```

This is a strict superset, in terms of covered wall-clock windows, of today's
`self._preparing or self._worker is not None`:
- The PREPARING and PARSING windows map onto the same real-world spans `_preparing` and
  `_worker is not None` covered before (worker construction through `parse_completed`/
  `parse_failed`), so no existing "busy" window shrinks.
- The APPLYING window is new coverage — exactly the gap identified in the requirements — with no
  corresponding removal of any previously-true window, so `is_busy()` cannot become `False` at any
  point where either old flag was `True` and the flow hasn't finished.

### Closing the gap without new re-entrancy risk

The gap closes because `_state` transitions to `APPLYING` **synchronously**, inside
`_on_parse_completed()`, strictly before `_finish_import()` is invoked, and transitions back to
`IDLE` **synchronously**, as the last statement inside `_finish_import()`, after all dialogs and
persistence work are done. Both the entry and exit of the APPLYING window are on the same call
stack as the work they bracket — there is no dependency on the worker's `finished` signal (whose
async timing relative to `parse_completed` was the root cause of the original bug) for either
edge. This removes the race entirely rather than narrowing it: `_state` has exactly one writer
active at a time (the GUI-thread callback currently executing), and `_worker`'s clearing in
`_on_worker_finished()` — however it interleaves with `parse_completed`/`parse_failed` handling —
no longer feeds into `is_busy()`, so its timing is irrelevant to correctness of the busy signal.

Re-entrancy check: `import_collections()`'s guard (`if self.is_busy(): return`) is evaluated at
the very top of that method, before any state mutation. Because `_state` is APPLYING for the
entire `_finish_import()` call (including while `_resolve_conflicts()` shows modal dialogs —
`prompt_collection_import_conflict` — which pump the Qt event loop and could otherwise allow a
re-entrant `import_collections()` call from another GUI trigger), a second `import_collections()`
call arriving during those modal dialogs now correctly sees `is_busy() is True` and is dropped —
this is the concrete instance of user scenario 4 ("re-entrant trigger while applying") that today
can slip through and after this change cannot. No new re-entrancy is introduced: `_set_state()` is
a plain synchronous attribute write plus the same button/status-message side effects
`_set_preparing()` already performs (which do not themselves re-enter `CollectionImportActions`),
and no code path sets `_state` from more than one place concurrently (everything runs on the GUI
thread; the worker thread never touches `_state`, `_preparing`, or `_worker` directly today and
continues not to).

### Interfaces / API surface

- **Public methods unchanged**: `is_busy()`, `wait_idle()`, `teardown()`, `import_collections()` —
  same signatures, same callers (`CollectionsPresenter` and tests), same return semantics (only
  `is_busy()`'s *value* changes for the previously-buggy APPLYING window, which is an intended
  bugfix, not an API change).
- **Removed private attribute**: `self._preparing` (replaced by `self._state`).
- **Renamed private method**: `_set_preparing(active: bool)` → `_set_state(state:
  CollectionImportState)`.
- **New private attribute**: `self._state: CollectionImportState`, defaulting to
  `CollectionImportState.IDLE` in `__init__`. This is the "expose/observe the new lifecycle state
  for testing purposes" surface the requirements' Definition of Done allows (`presenter._state`
  is accessible the same way `presenter._preparing`/`presenter._worker` are accessible today —
  no new public property is added, since the requirements only ask for internal state tracking to
  become explicit, not for a new public API).
- **Unchanged private attribute**: `self._worker` — same type, same lifecycle, same call sites for
  writes (`_start_parse`, `_on_worker_finished`, `teardown`), now purely for QThread mechanics.
- **New Qt-free module**: `pypost/core/collection_import_state.py` exporting
  `CollectionImportState`.

## Q&A

- **Q: Why not transition to PARSING inside `_on_parse_progress()` (first progress signal) instead
  of immediately after `worker.start()`?**
  A: `_on_parse_progress` may never fire (e.g. a very small/fast import, or a worker that emits
  only `parse_completed`/`parse_failed`) — gating the PARSING transition on it would leave a
  window right after `start()` where `_state` is still PREPARING despite the worker already
  running, which is functionally fine for `is_busy()` (still non-IDLE) but muddies the "PARSING
  means worker running" semantics for no benefit and adds a dependency on a signal that isn't
  guaranteed to fire. Transitioning right after `worker.start()` is simpler, always correct, and
  matches the requirements' wording ("parsing: background parse worker running").
- **Q: Should `_finish_import()` take the target state as a parameter or read `self._state`
  itself?**
  A: Neither — `_finish_import()` doesn't need to touch `_state` except to reset it to IDLE at the
  end; the APPLYING transition happens in its caller (`_on_parse_completed`) right before the
  call, keeping `_finish_import()`'s existing signature (`collections`, `parse_errors`) and
  responsibilities (conflict resolution, planning, persisting, refresh) untouched apart from one
  added trailing statement.
- **Q: Does `CollectionImportState` need an explicit failure/error member (e.g. `FAILED`)?**
  A: No — per requirements scenario 5 and the current code, a parse failure or "no valid
  collections" result returns straight to IDLE after showing an error dialog; there is no
  persistent "error" stage to track, matching today's behavior of `_set_preparing(False)` in both
  `_on_parse_completed`'s empty-collections branch and all of `_on_parse_failed`. Adding a FAILED
  state would be new behavior/API surface beyond what Step 1 scoped.
