# PYPOST-1229: Implement cooperative worker thread cancellation for CollectionImportWorker

## Goals

Today, once a collection import file starts parsing on the background worker thread, the parse
runs to completion no matter what the user does in the UI. Closing the import panel or otherwise
cancelling the import does not actually stop the in-flight parse work — it only asks the worker
to stop and then waits a short, fixed amount of time for it to finish on its own before giving up.

For small import files this is invisible. For large import files (many collection records) it
means:

- The user cannot actually abort a long-running import once it has started — closing the panel
  does not free the CPU/IO work the parse is doing, it just stops the UI from watching it.
- The app can appear to hang or remain busy for longer than necessary after the user has already
  indicated (by closing the panel or cancelling) that they no longer want the result.
- Panel teardown has to guess how long to wait for the worker rather than being able to rely on
  the worker actually stopping promptly when asked.

The business goal is a responsive, trustworthy "Import Collections" feature: when the user closes
the import panel or cancels an import, the underlying work should actually stop promptly, instead
of silently continuing in the background and only stopping once the user forgets they own the CPU
cycles they are paying for. This directly improves perceived responsiveness and avoids wasted work
on parses whose results will never be used.

## User Stories

- As a user importing a large collection file, when I close the import panel or cancel the
  import, I want the parsing work to stop promptly, so that the application does not keep working
  on a result I no longer want and I am free to do something else immediately.
- As a user, when I cancel an import mid-parse, I want the panel to close/reset in a bounded,
  predictable amount of time rather than potentially waiting for an arbitrarily long parse to
  finish on its own.
- As a developer working on the collections import feature, I want cancellation of an in-flight
  import to be verifiable by an automated test, so that regressions in cancel behavior are caught
  before release.

## Definition of Done

- When the user closes the import panel, or otherwise cancels an in-progress import, while a
  parse is running, the parse work stops cooperatively at the next safe checkpoint instead of
  continuing to completion.
- The user-visible effect of cancellation is prompt: the panel/teardown no longer depends on the
  entire remaining file being parsed before it can proceed, for files large enough that this
  currently causes a noticeable delay.
- Cancelling an import that has already produced a result (parse completed, applying to the
  collection tree) does not need to be interrupted — cancellation applies to in-flight parse work,
  not to already-finished application of results. (Confirm with stakeholder review if apply-time
  cancellation is also in scope; current default assumption is parse-time only, matching the
  ticket's "immediate abort upon panel closure or import cancellation" wording, which today is
  only observable during the parse stage.)
- No regression to existing import behavior: parsing a file to completion without cancellation
  still produces the same collections/parse-errors/results as before.
- No regression to existing panel-teardown behavior for the already-covered case (worker finishes
  or is waited on) documented in PYPOST-1182.
- An automated test demonstrates that a long-running import parse, when cancelled mid-flight,
  stops promptly rather than running to completion. (This closes the "Worker Cancellation on Early
  Teardown" gap called out as missing test coverage in the PYPOST-1182 tech-debt analysis.)

## Task Description

**Problem.** The collection import feature runs file parsing on a background `QThread` so the
GUI stays responsive while a file is read and validated. Today, when the panel is torn down (on
close, or on explicit import cancellation) while that parse is running, the code that manages the
worker does ask the thread to stop, then gives it a short, fixed grace period to finish before
moving on regardless of whether it actually stopped. Investigation of the current worker
confirms it has no mechanism to notice such a stop request while it is busy parsing a file — the
parse routine runs a single record-by-record loop from start to finish with no checkpoint that
looks at whether cancellation has been requested. As a result, the request to stop does not
actually shorten the parse for any file large enough that the grace period elapses before parsing
finishes; the parse keeps running in the background regardless, and the app is left waiting past
its usual teardown budget or "letting go" of a still-running background job.

**Goal.** Make the parsing work stop promptly, on a best-effort basis, when the user closes the
import panel or cancels the import while parsing is underway — instead of the current
"ask and hope, then give up waiting" behavior with no effect on the actual work being done.

**Constraints and assumptions.**

- This is a tech-debt follow-up identified during PYPOST-1182 and tracked as a specific follow-up
  item ("Implement cooperative worker thread cancellation ... to allow immediate abort upon panel
  closure") in that ticket's tech-debt analysis. It targets the parse worker specifically, not the
  conflict-resolution or apply stages of import, which already run entirely on the GUI thread and
  are not backgrounded.
- The fix must be cooperative: the parse work must periodically notice a stop request and end
  itself early, rather than the surrounding code forcibly killing the thread. Forcible termination
  of a running thread is out of scope and is not an acceptable behavior for this feature.
  (Whether "periodically" is per-record, per-batch, or on another cadence is an architecture/
  implementation decision for Step 2, not a business requirement — this document only requires
  that a reasonably prompt, bounded checkpoint exists.)
- Cancelling before any results are produced must not surface as an error to the user, nor should
  it write partial or misleading results into the collection tree; a cancelled import should look
  and feel like "nothing happened," not "something failed."
  (Note: this behavior does not yet exist. Whether it is delivered fully in this ticket or split
  further is an architecture decision for Step 2.)
- This ticket does not change how the user initiates cancellation (panel close, cancel action) —
  those triggers already exist. It only changes whether the underlying work actually stops when
  those triggers fire.
- Out of scope: changing the fixed teardown/wait timeout value itself (tracked separately as
  pre-existing tech debt), extracting shared test-wait helpers (PYPOST-1230), and the
  `CollectionImportState` state-machine refactor (already completed under PYPOST-1228).
- Programming language: Python (matches the rest of the `pypost` codebase; the affected code is a
  `PySide6`/Qt-based desktop application module).

## Main Entities

- **Collection Import**: the end-to-end user operation of picking a file, parsing it into
  candidate collections, resolving name conflicts, and applying accepted collections into the
  workspace. Has an in-flight state while parsing.
- **Import Parse Worker**: the background unit of work that reads and validates an import file
  into candidate collections, off the GUI thread, so the interface stays responsive during
  parsing.
- **Cancellation Request**: the user's signal — via closing the import panel or explicitly
  cancelling — that they no longer want the current import's parse work to continue.
- **Import Result**: the outcome shown to the user after a completed import (collections added,
  updated, skipped, renamed, and any parse errors). A cancelled import produces no result to
  display.

## Q&A

- **Q: Does the parse worker currently check for a stop/interruption request at any point while
  running?**
  A: No. Reviewed `pypost/core/qt/collection_import_parse_worker.py`: its `run()` method calls the
  injected file-reading routine once and waits for it to return (emitting progress and result
  signals along the way); nothing in `run()` or in the per-record parse loop it calls into
  (`load_collection_import_candidates` in `pypost/core/collection_import.py`) ever inspects
  whether a stop has been requested. The parse loop does already call an `on_progress` callback
  once per record, which is a natural existing checkpoint in the work, but that callback is
  currently only used to report progress to the UI, not to check for a stop request.

- **Q: What happens today when the user closes the panel or cancels an import while parsing is
  in progress?**
  A: The presenter-side orchestration (`CollectionImportActions.teardown()` in
  `pypost/ui/presenters/collection_import_actions.py`, added under PYPOST-1228's state-machine
  work) requests that the worker stop, then waits up to a short fixed grace period for it to
  finish, disconnects its signals either way, and marks the import idle regardless of whether the
  worker actually stopped in time. Because the worker itself never notices the stop request, this
  wait either "gets lucky" (the parse happened to finish anyway) or times out and the presenter
  moves on while the parse thread is still running in the background.

- **Q: Is this only about panel closure, or also explicit "cancel" during an import?**
  A: Both, per the Jira description ("immediate abort upon panel closure or import cancellation").
  In the current UI both paths converge on the same teardown/stop mechanism, so both are affected
  the same way by the missing checkpoint.

- **Q: Does this affect the conflict-resolution or apply stage of import?**
  A: No. Those stages already run synchronously on the GUI thread after parsing completes; there
  is no background worker to cancel during them. This ticket is scoped to the parse stage.

- **Q: Where did this requirement originate?**
  A: `ai-tasks/PYPOST-1182/60-tech-debt.md`, under "Follow-up Tasks": "Implement cooperative
  worker thread cancellation (`QThread.requestInterruption()`) for `CollectionImportWorker` to
  allow immediate abort upon panel closure," filed as PYPOST-1229. The same document also lists
  "Worker Cancellation on Early Teardown" under "Missing Tests" as a currently-uncovered scenario,
  which this ticket's Definition of Done addresses.
