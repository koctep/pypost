# PYPOST-1229: Implement cooperative worker thread cancellation for CollectionImportWorker

## Research

**Call chain (confirmed by direct source reading).**

```
CollectionImportActions._start_parse()          (GUI thread, collection_import_actions.py)
  -> CollectionImportParseWorker(path, read_import_file).start()
       -> QThread.run()                          (worker thread, collection_import_parse_worker.py:55)
            -> self._read_import_file(path, on_progress=_emit_progress)
                 -> load_collection_import_candidates(path, on_progress)  (core/collection_import.py:153)
                      for index, record in enumerate(records, start=1):
                          ...
                          if on_progress is not None:
                              on_progress(index, total_records)   # <-- fires once per record
```

- `CollectionImportParseWorker.run()` (`pypost/core/qt/collection_import_parse_worker.py:55-90`) calls
  `self._read_import_file` exactly once, synchronously, then emits `parse_completed` or
  `parse_failed`. It never reads `self.isInterruptionRequested()` anywhere.
- The only per-item checkpoint anywhere in the parse path is the `on_progress` callback invoked by
  `load_collection_import_candidates` after each record is processed
  (`pypost/core/collection_import.py:180` and `:187`). `load_collection_import_candidates` is
  Qt-free by design (module docstring: "No Qt and no storage dependency") and must stay that way —
  it does not know about `QThread` or interruption, it only calls `on_progress(index, total)` if a
  callback was supplied.
- The worker's `_emit_progress` closure (`collection_import_parse_worker.py:58-59`) is what
  `_read_import_file` actually receives as `on_progress` when `_callable_accepts_progress` detects
  the parameter (`_callable_accepts_progress`, lines 20-39). It is invoked on the worker thread,
  from inside `run()`'s call stack — i.e. `_emit_progress` executes on `self` (the `QThread`
  instance) *from the thread it belongs to*.
- `CollectionImportParseWorker` is instantiated in exactly one place in production code:
  `CollectionImportActions._start_parse()` (`collection_import_actions.py:174`), with
  `read_import_file` ultimately defaulting to `load_collection_import_candidates`
  (`collections_presenter.py:72`). The env-import dialog uses a different, unrelated
  `read_import_file` implementation and does not use this worker class at all — so this design
  only needs to reason about the collections import path.
- `CollectionImportActions.teardown()` (`collection_import_actions.py:117-158`) already calls
  `worker.requestInterruption()` then `worker.wait(100)` before disconnecting signals and reaping
  the worker. `requestInterruption()` runs on the GUI thread; `isInterruptionRequested()` is
  documented by Qt as safe to call from either the requesting thread or the thread being
  interrupted (it just reads an atomic flag) — no mutex/lock is needed on either side.
- `CollectionImportActions` currently reacts to exactly three worker signals:
  `parse_progress -> _on_parse_progress`, `parse_completed -> _on_parse_completed`,
  `parse_failed -> _on_parse_failed`, plus Qt's built-in `finished -> _on_worker_finished`.
  `_on_parse_completed` with an empty `collections` list already shows an "invalid file" error
  dialog, and `_on_parse_failed` always shows an error dialog — so routing a *cancellation*
  through either existing signal would either produce a misleading result dialog or a misleading
  error dialog. The Definition of Done explicitly requires a cancelled import to "look and feel
  like nothing happened."

**Conclusion: `on_progress` is the right injection point.** It already fires once per record (a
reasonably fine cadence — matches the ticket's "per-record, per-batch, or another cadence" framing
without adding a new callback plumbing path through `load_collection_import_candidates`), it
already runs on the worker thread inside `run()`'s call stack, and it is the only place in the
current call chain that executes repeatedly during a long parse. No change to
`load_collection_import_candidates`'s signature or to `core/collection_import.py` is needed — it
stays Qt-free; the worker's own `on_progress` wrapper does the interruption check and turns it into
control flow the worker understands.

## Implementation Plan

1. **New exception, worker-owned.** Add `class CollectionImportCancelled(Exception)` to
   `pypost/core/qt/collection_import_parse_worker.py` (not to `core/collection_import.py`, which
   stays Qt-free and never needs to know this type exists — it only ever propagates it unseen
   through its `on_progress(...)` call).
2. **Check-and-raise in the existing progress wrapper.** In `CollectionImportParseWorker.run()`,
   change the `_emit_progress` closure so that, after emitting `parse_progress`, it checks
   `self.isInterruptionRequested()` and raises `CollectionImportCancelled` if true:
   ```python
   def _emit_progress(done: int, total: int) -> None:
       self.parse_progress.emit(done, total)
       if self.isInterruptionRequested():
           raise CollectionImportCancelled()
   ```
   This raise unwinds through `load_collection_import_candidates`'s loop (an ordinary Python
   exception propagating out of a callback call — no special handling required there since it
   doesn't catch anything around `on_progress(...)`), then out of `self._read_import_file(...)`,
   and into `run()`'s existing `try` block.
   - Also add one check before the loop even starts (or accept that a zero-progress-call file —
     empty `records` — simply finishes; that's correct, there is nothing to cancel).
3. **New signal + dedicated except branch.** Add `parse_cancelled = Signal()` alongside
   `parse_completed`/`parse_failed`. In `run()`, add an `except CollectionImportCancelled:` branch
   *before* the existing `except Exception:` branch (must come first — `CollectionImportCancelled`
   is a plain `Exception` subclass and would otherwise be swallowed by the generic handler and
   misreported as a failure):
   ```python
   except CollectionImportCancelled:
       logger.info("collection_import_parse_worker_cancelled path=%s", self._path)
       self.parse_cancelled.emit()
   ```
   No traceback (`exc_info`), no warning/error level — cancellation is an expected, user-initiated
   outcome, not a fault.
4. **New signal handling in `CollectionImportActions`.**
   - Connect `worker.parse_cancelled` to a new `_on_parse_cancelled` slot in `_start_parse()`,
     alongside the existing three connections.
   - `_on_parse_cancelled(self) -> None` sets state back to `CollectionImportState.IDLE` (same as
     the other two terminal handlers) and does *nothing else* — no dialog, no `_finish_import`,
     no tree refresh. This is what makes a cancelled import "look like nothing happened."
   - Disconnect `parse_cancelled` in `teardown()` alongside the other three signal disconnects
     (same try/except RuntimeError/TypeError pattern already used there).
   - No change to `teardown()`'s `requestInterruption()` / `wait(100)` sequence itself (the fixed
     100ms timeout value is explicitly out of scope) — but its effect changes: previously
     `wait(100)` almost never actually observed the worker stop for a large file; after this
     change the worker checks the flag every record, so for any file where per-record work is fast
     relative to 100ms, the worker now genuinely exits within that window instead of only "getting
     lucky." Cases where a single record's processing exceeds the wait budget are an accepted
     residual latency, consistent with "cooperative, best-effort" as scoped by the ticket.
5. **No change to `core/collection_import.py`.** `load_collection_import_candidates` keeps its
   current signature and stays exception-and-Qt-agnostic; it is exercised as-is by existing unit
   tests with no interruption concept leaking into that pure module.
6. **No change to `_callable_accepts_progress`/signature detection.** The cancellation checkpoint
   depends on `on_progress` being supplied, which is already the production path for the only
   caller of this worker (`collections_presenter.py` defaults `read_import_file` to
   `load_collection_import_candidates`). A hypothetical injected `read_import_file` that doesn't
   accept `on_progress` simply cannot be interrupted mid-parse — same limitation exists implicitly
   today and is out of scope to change.

**Mandatory — Failing Repro (next Step 3):** Write a red test that starts a
`CollectionImportParseWorker` against an injected `read_import_file` stand-in whose per-record work
is slow enough to observe (e.g. a fake `read_import_file(path, on_progress=...)` that loops many
"records" calling `on_progress` with a small sleep or a record count high enough that interruption
happens well before natural completion), calls `worker.requestInterruption()` partway through (from
the GUI/test thread, e.g. triggered on the first `parse_progress` emission via a
`QSignalSpy`/connected slot, or after a short `QThread.msleep` once the worker has started), then
asserts:
- `worker.wait(<a few hundred ms, well under a full synthetic run>)` returns `True` — the thread
  actually stops promptly instead of running to completion.
- `parse_cancelled` was emitted exactly once.
- `parse_completed` and `parse_failed` were **not** emitted.
- The total elapsed time from `requestInterruption()` to thread stop is small relative to what a
  full uninterrupted run of the fake `read_import_file` would take (proving cancellation actually
  shortened the work, not just that the thread happened to finish naturally).

This test must fail today because `CollectionImportCancelled`/`parse_cancelled` do not exist yet
and `run()` never checks `isInterruptionRequested()` — `worker.wait(...)` will time out and
`parse_completed` (or `parse_failed`, depending on the fake) will fire instead. It lives under
`tests/` alongside the existing `collection_import_parse_worker`/`collection_import_actions` test
files (exact path to be finalized in Step 3, following this repo's existing test layout for that
module) and needs no live external dependency — the fake `read_import_file` is a plain Python
function.

A second test (or an extension of `CollectionImportActions.teardown()`'s existing coverage) should
demonstrate that `teardown()` observes `wait_idle`/`teardown()` completing without the old
"clean=False" grace-period timeout path when a slow parse is interrupted — this is the scenario
named "Worker Cancellation on Early Teardown" in the PYPOST-1182 tech-debt notes. Whether this is a
second dedicated test or folded into the first is a Step 3 detail, not an architecture decision.

## Architecture

### Modules touched

| Module | Role | Change |
| --- | --- | --- |
| `pypost/core/qt/collection_import_parse_worker.py` | Background `QThread` subclass that runs the injected `read_import_file` off the GUI thread. | Add `CollectionImportCancelled` exception, add `parse_cancelled` signal, add interruption check inside the existing `_emit_progress` callback, add a dedicated `except` branch in `run()`. |
| `pypost/core/collection_import.py` | Pure, Qt-free file-parsing/validation/planning logic. Owns the per-record loop and the existing `on_progress` callback contract. | **No change.** Confirms the callback boundary is the correct and sufficient seam — `on_progress` already exists, is already called every record, and is already the only repeating checkpoint in the whole call chain. |
| `pypost/ui/presenters/collection_import_actions.py` | GUI-thread orchestration: owns the worker's lifecycle, its state machine (`CollectionImportState`), and `teardown()`. | Connect/disconnect the new `parse_cancelled` signal; add `_on_parse_cancelled` slot that resets to `IDLE` with no dialog and no result. |

### Interaction / sequence (interrupted case)

```
GUI thread                              Worker thread
-----------                             -------------
_start_parse()
  worker.start() ------------------------> run()
                                             _read_import_file(path, on_progress=_emit_progress)
                                               load_collection_import_candidates loop:
                                                 record 1 -> on_progress(1, N)
                                                              -> parse_progress.emit(1, N)
                                                              -> isInterruptionRequested()? No
                                                 record 2 -> on_progress(2, N)  ... etc.
teardown() (user closes panel / cancels)
  requestInterruption()  ---sets atomic flag--->
  wait(100)                                    record k -> on_progress(k, N)
                                                              -> parse_progress.emit(k, N)
                                                              -> isInterruptionRequested()? YES
                                                              -> raise CollectionImportCancelled
                                             run() catches CollectionImportCancelled
                                               -> parse_cancelled.emit()
                                               -> run() returns, thread finishes
  wait(100) returns True (thread has stopped)
  worker.parse_cancelled disconnected (already fired before disconnect, harmless either order)
  _set_state(IDLE)
```

Because `_emit_progress` executes synchronously *inside* `run()`'s call stack on the worker thread,
`isInterruptionRequested()` is being called by the thread on itself — the case Qt explicitly
documents as safe with no locking required. `requestInterruption()` on the GUI thread and the read
in `_emit_progress` on the worker thread only ever touch Qt's own atomic interruption flag; no new
shared mutable state is introduced by this design, so no new mutex/lock is needed anywhere.

### Signal contract (before / after)

| Signal | Meaning before | Meaning after |
| --- | --- | --- |
| `parse_completed(collections, parse_errors)` | Parse ran to completion (possibly with zero valid collections, handled by `_on_parse_completed`). | **Unchanged.** Never emitted for a cancelled run. |
| `parse_failed(error)` | Parse raised `CollectionImportFileError` or any other `Exception`. | **Unchanged**, except `CollectionImportCancelled` is now caught in its own branch *before* the generic `except Exception`, so a cancellation can no longer be misreported through this signal. |
| `parse_cancelled()` *(new)* | did not exist | Emitted exactly once, only when `isInterruptionRequested()` was observed true from inside the parse loop. Mutually exclusive with `parse_completed`/`parse_failed` for a given run. |

This three-way split is what prevents `collection_import_actions.py`'s callers from misinterpreting
a cancelled run as either success (`parse_completed`, which would otherwise trigger conflict
resolution and `_finish_import` — writing into the collection tree from a run the user already
abandoned) or failure (`parse_failed`, which would otherwise pop an error dialog for something the
user deliberately stopped, contradicting the Definition of Done's "should look and feel like
nothing happened, not something failed").

### Why not a return-value / partial-result approach

An alternative would be having `load_collection_import_candidates` (or the worker) return a
sentinel/partial-result tuple instead of raising. Rejected because:
- It would require threading an interruption-aware return type through the Qt-free
  `core/collection_import.py`, coupling pure logic to a Qt-thread concept it has no other reason to
  know about.
- Python's normal idiom for "abandon the rest of this call and unwind" from inside a callback is an
  exception; `run()` already has a `try/except` structure built exactly for turning "how this parse
  ended" into one of the two existing terminal signals, so adding a third `except` branch is the
  smallest, most consistent extension of that existing structure.
- A raised exception guarantees the loop cannot accidentally keep running and emit further
  `parse_progress` ticks or, worse, reach `parse_completed` after interruption was observed —
  control leaves the loop immediately, at the exact record where the flag was seen.

## Q&A

- **Q: Should the interruption check live inside `load_collection_import_candidates` itself
  instead of the worker's `on_progress` wrapper?**
  A: No. `core/collection_import.py`'s module docstring states it is deliberately Qt-free and
  independently unit-testable without `QApplication`. `QThread.isInterruptionRequested()` is a Qt
  concept; introducing it there would break that boundary for no benefit, since the worker's own
  `on_progress` callback already gets called at the same cadence and already has access to `self`
  (the `QThread`).

- **Q: Does checking `isInterruptionRequested()` from `_emit_progress` need a lock, given it runs
  on the worker thread while `requestInterruption()` is called from the GUI thread?**
  A: No. Qt's `QThread` interruption flag is documented as safe to set from any thread
  (`requestInterruption()`) and safe to read from any thread, including the thread being
  interrupted (`isInterruptionRequested()`); it is a simple atomic flag with no user-visible
  locking API and none is needed here. This task's design introduces no additional shared mutable
  state between the two threads beyond that existing Qt primitive.

- **Q: What about the case where the parse has already progressed to `parse_completed` and
  `CollectionImportActions` has moved into `APPLYING` (conflict resolution / applying to the tree)
  by the time cancellation is requested?**
  A: Out of scope per the requirements doc ("cancellation applies to in-flight parse work, not to
  already-finished application of results"). `parse_cancelled` can only ever be emitted from inside
  `run()`, before `parse_completed`/`parse_failed` — once the worker thread has emitted one of
  those and returned, there is nothing left running to cancel. No architecture change needed for
  the applying stage.

- **Q: Could the worker check `isInterruptionRequested()` in more places than just
  `_emit_progress` (e.g. also once at the very top of `run()`, before calling
  `_read_import_file` at all)?**
  A: Optional, low-cost addition worth including in Step 4: an early check at the top of `run()`
  handles the edge case where `requestInterruption()` was called between `worker.start()` and the
  thread actually beginning to execute — otherwise a race where the whole file is small enough to
  finish before the first `on_progress` call could still run to completion even though
  interruption was already requested. This is a straightforward extra `if
  self.isInterruptionRequested(): ...; return` guard at the top of the existing `try` block; it
  does not change the signal contract or module boundaries described above, so it does not affect
  this document's design, only its Step 4 implementation detail.

- **Q: Does this change `CollectionImportState`?**
  A: No new state is needed. A cancelled parse simply returns to `IDLE`, the same terminal state
  used today after a successful or failed import — from the state machine's point of view,
  "parsing stopped" is `IDLE` regardless of why. The distinction that matters (no dialog shown) is
  handled entirely by which slot (`_on_parse_cancelled` vs. the existing two) reacts to which
  signal, not by a new state value.
