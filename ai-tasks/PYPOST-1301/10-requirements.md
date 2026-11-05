# PYPOST-1301: Guard WebSocket stream export teardown on tab removal and app exit

## Goals

API developers use PyPost WebSocket tabs to capture live traffic and export transcripts
(JSON or plain text) for debugging. Export runs as background work owned by the stream
view so the UI stays responsive. PYPOST-1286 added an export-safe disposal contract on
the stream view: before the view is disposed, export ownership must finish within a
bounded wait, and disposal is refused while that work is still owned.

That contract is never reached on real product paths. Closing a WebSocket tab removes
the tab from the tab strip only. The page stays alive and hidden until process exit,
export teardown is never invoked, and the page is never deleted. A running export can
still finish after the tab is removed, which masks the gap during normal use. The
business risk appears when the user quits the application while an export is still
owned: the background export worker has no durable owner beyond the leaked view, so
process teardown can destroy it while it is still running. That can abort the app with
a hard thread-destruction failure and can leave the transcript file incomplete or
unusable.

This task closes that gap so tab removal and application exit both attempt
export-safe teardown with a bounded wait, dispose of the page safely when ownership
ends in time, and prove the real paths with automated regression coverage. Tab close
and app exit share the bounded-wait attempt; they differ only after the budget is
exhausted (deferral while the process lives vs abandon so exit can finish). It is the
Medium follow-up TD-1 from [PYPOST-1286 technical debt](../PYPOST-1286/60-tech-debt.md).

## User Stories

- As an API developer closing a WebSocket tab while a transcript export is running, I
  want the tab to leave the strip promptly and the stream view to run export-safe
  teardown, so the export is finished within a bounded wait when possible, and if it
  is still owned after that wait the underlying page stays alive only until ownership
  ends (deferred disposal)—not leaked forever with no teardown.
- As an API developer closing a WebSocket tab when no export is running, I want the tab
  removed and the page disposed without extra delay or leftover hidden pages.
- As an API developer quitting PyPost while a WebSocket transcript export is still
  running, I want application exit to wait for export-safe teardown within a bounded
  budget so that, when ownership ends in time, the export completes or fails cleanly
  and exit does not abort by destroying a still-running export worker. If ownership
  remains after that budget, I want the process to release export ownership and exit
  without a hard abort, accepting that the in-flight transcript may be incomplete or
  abandoned rather than hanging shutdown or requiring mid-write cancel UX.
- As an API developer quitting when no WebSocket export is busy, I want exit to take no
  added delay from stream-view export teardown.
- As a maintainer, I want automated regression coverage that exercises tab removal and
  application exit while a stream export is owned, proving the production disposal
  paths rather than only synthetic direct disposal of the stream view.

## Definition of Done

1. **Tab removal invokes export-safe teardown.** Closing a WebSocket tab (and the shared
   generic tab-close path that removes pages the same way) runs the stream view's
   export-safe cleanup before the page is considered disposed. Teardown is no longer
   unreachable from production tab removal.
2. **Busy export on tab removal: bounded wait, then defer.** When an export is still
   owned at tab removal, teardown waits only within the existing close wait budget. If
   the export finishes in time, ownership is released and disposal may proceed. If it
   does not, disposal of that page is deferred until ownership ends (the tab may still
   leave the strip so the user is not blocked). Deferral applies only while the
   application process continues to run.
3. **Idle tab removal disposes the page.** When no export is owned, removing the tab
   deletes the page safely so it does not remain leaked and hidden until process exit.
4. **Application exit attempts the same bounded cleanup.** Quitting the application
   while a WebSocket stream view still owns an export runs export-safe teardown with a
   bounded wait. If ownership ends within the budget, disposal proceeds and exit does
   not destroy a still-running export worker.
5. **Exit after budget: abandon ownership, then proceed.** If export ownership remains
   after the exit wait budget, the application releases that ownership for process exit
   (abandon / orphan policy). Exit must complete without hanging indefinitely and
   without a hard "destroyed while still running" abort attributable to the stream
   export worker. The abandoned in-flight transcript is not required to be complete or
   usable; completeness is guaranteed only when ownership ends within the budget.
6. **No crash from export-worker destruction at exit.** Application exit during an
   active stream transcript export must not fail with a hard "destroyed while still
   running" abort attributable to the stream export worker—whether ownership ended in
   time or was released under the abandon policy after the budget.
7. **Export outcome integrity (by path).** An export that finishes within the teardown
   wait produces a complete usable transcript. On tab removal after budget exhaustion,
   deferred disposal stays safe until ownership ends and the eventual finish remains
   usable. On app exit after budget exhaustion, the abandoned export may leave an
   incomplete file; the required outcome is safe process exit, not a complete file.
8. **Regression coverage for real paths.** Automated tests cover (a) WebSocket tab
   removal during an owned export and (b) application exit during an owned export,
   exercising the production close/removal paths—not only direct synthetic disposal of
   the stream view. Tests use explicit timeouts and bounded waits.
9. **Idle path regressions.** Automated coverage also shows that tab removal and exit
   with no busy export dispose cleanly without added wait.
10. **Preserved export UX.** Starting, completing, and failing exports for open tabs
    remain unchanged when the user is not closing the tab or quitting. Public export
    busy-state and wait helpers from PYPOST-1286 remain available.
11. Repository gates run through `make` targets; no new failures are attributable to
    this task. Documentation and code lines stay within the 100-character limit.

## Task Description

### Problem

PYPOST-1286 defined export-safe disposal on the WebSocket stream view: cleanup waits a
bounded time for export ownership to end, and close is refused while ownership remains.
Those behaviors are exercised only by tests that dispose the view directly. Product tab
close removes the tab from the strip and never asks the stream view to clean up or
delete the page. The removed page and its export ownership therefore survive as a
hidden leak until process exit. Under normal post-close export completion the leak is
easy to miss. On application quit with an export still owned, the worker that writes
the transcript has no durable owner beyond that leaked view, so process teardown can
destroy it while it is still running and abort the exit or leave a bad export file.

### Business reason

Users must be able to close WebSocket tabs and quit the app without crashing shutdown
or leaving indefinite teardown hangs. Maintainers need the existing export-safe
disposal attempt on the paths users actually take, with regression proof for those
paths. Tab close may defer page disposal after the wait budget because the process
keeps running. App exit cannot defer forever: after a bounded wait it must release
ownership and proceed, even if that abandons an unfinished transcript. Leaving the
guard only on synthetic disposal keeps Medium tech debt from PYPOST-1286 open and
leaves a real exit-time failure mode.

### Implementation language

Python.

### Scope

- Route WebSocket tab removal through the stream view's export-safe cleanup, including
  the dedicated WebSocket close path and the generic tab-close path that removes pages
  the same way.
- Ensure application exit / main-window teardown also attempts export-safe cleanup for
  stream views that still own an export, within a bounded wait.
- Dispose removed pages safely when cleanup succeeds within the budget; on tab removal,
  defer page disposal while export ownership remains after the bounded wait.
- On application exit, if ownership remains after the exit wait budget, release
  ownership so the process can exit without a hard abort (abandon / orphan of the
  in-flight export)—without adding interruptible mid-write or cancel UX.
- Automated regression for tab removal and app exit during an owned export, plus idle
  removal/exit without a busy export.
- Preserve existing export start/finish/fail behavior for tabs that remain open.

### Out of scope

- Changing transcript file formats, export menu labels, or the export worker's write
  algorithm beyond what teardown safety requires.
- Making export interruptible mid-write as a product capability, or adding
  user-facing cancel UI for export (unless already present). Coordinating teardown
  and disposal around the existing ownership model remains in scope; the exit-time
  abandon / ownership-release after the wait budget is an allowed shutdown outcome,
  not a general cancel feature.
- Broader main-window shutdown redesign for unrelated participants (history,
  environment, collections, and so on), except as needed to include stream-view export
  teardown on exit.
- Extracting shared worker-hold test helpers (tracked as PYPOST-1304).
- Unrelated flaky-test or lint-scope debt from PYPOST-1286 (PYPOST-1302, PYPOST-1303,
  and similar).

### Functional requirements

- Tab removal of a WebSocket page always attempts export-safe cleanup on the stream
  view before final page disposal.
- While an export is owned, cleanup waits only within the established close wait
  budget and does not hang indefinitely.
- If ownership remains after that budget on tab removal, the page is not
  force-destroyed; disposal is deferred until ownership ends (process still running).
- If no export is owned, tab removal deletes the page so it does not leak until exit.
- Application exit attempts the same export-safe cleanup for any stream view that
  still owns an export, within a bounded wait.
- If ownership ends within the exit budget, exit proceeds without destroying a
  still-running stream export worker, and a finished export remains usable.
- If ownership remains after the exit budget, ownership is released so exit can
  proceed without hang or hard abort; the abandoned export need not be complete.
- Regression tests exercise production tab-removal and app-exit paths under busy and
  idle export conditions.

### Non-functional requirements

- Teardown waits remain bounded; tab close and app exit must not hang indefinitely on
  export ownership.
- After the exit wait budget, process exit proceeds (via ownership release / abandon)
  rather than waiting for the export to finish.
- Idle tab removal and idle exit add no meaningful delay from export teardown.
- Diagnostics about export teardown must not include transcript payload content.
- Behavior remains deterministic under automated tests with explicit timeouts.

### Constraints and assumptions

- The stream view already exposes export busy-state, bounded wait, and cleanup entry
  points from PYPOST-1286; the gap is that production tab removal and app exit never
  call them.
- Closing a tab today only removes it from the strip; the page is not deleted and
  cleanup is never invoked—this task must change that outcome, not only document it.
- A running export after tab removal can still finish today; that incidental success
  must not be treated as proof that teardown is wired correctly.
- Tab close and app exit share a bounded-wait teardown attempt; post-budget outcomes
  differ by lifecycle: defer disposal while the process lives; release ownership so
  exit can finish when the process is quitting.
- Abandoning an in-flight export at exit after the budget is an accepted business
  trade-off: safe exit without hang or hard abort outweighs guaranteeing transcript
  completeness in that edge case.
- The primary user-visible failure mode to prevent is unsafe or unbounded process exit
  during a busy export (hard abort / indefinite hang), with leaked hidden pages as a
  secondary maintainability cost.
- Measurements and waits are not hard real-time guarantees under OS stalls or resource
  exhaustion.
- All verification runs through Make targets per `AGENTS.md`.

## Main Entities

- **WebSocket tab / page**: the UI unit the user opens for a WebSocket session and can
  close from the tab strip.
- **Stream view**: the WebSocket stream UI that owns transcript display and export.
- **Stream transcript export**: background work that writes a JSON or plain-text
  transcript file for the current stream.
- **Export ownership**: the stream view's claim that an export worker is still running
  or not yet fully released.
- **Export-safe teardown**: the bounded wait for ownership to end before the stream
  view page is destroyed; post-budget behavior depends on whether the process is
  continuing (defer) or exiting (release / abandon).
- **Tab removal**: the user or presenter action that takes a page out of the tab strip.
- **Application exit**: quitting PyPost / closing the main window such that process
  teardown begins.
- **Deferred page disposal**: on tab removal only—keeping a removed page alive until
  export ownership ends, then deleting it safely while the process still runs.
- **Abandoned export at exit**: an in-flight transcript whose ownership is released
  after the exit wait budget so the process can finish; completeness is not required.
- **Regression path**: an automated scenario that closes a tab or exits the app while
  export is owned, using the same product entry points users hit.

## Q&A

This is an autonomous run (sprint-task-runner); clarifying questions were resolved from
the Jira issue and PYPOST-1286 TD-1 rather than left open for interactive approval.

- **Why is this needed?** Export-safe disposal from PYPOST-1286 never runs on real tab
  close or app exit. Tab close leaks the page; app exit during a busy export can abort
  the process. Users and maintainers need the teardown attempt on the paths they
  actually use, with a clear post-budget policy for exit.
- **Is tab close alone the crash trigger?** No. After tab removal a running export can
  still finish because the page is leaked, not destroyed. The sharp failure is app exit
  (or any path that destroys the view) while export ownership remains. Tab removal must
  still invoke teardown so pages are not leaked and exit is not left holding hidden
  ownership.
- **Must the user wait for export before the tab leaves the strip?** No. The tab may
  leave the strip promptly. Disposal of the underlying page waits for ownership within
  the budget and is deferred if still busy—so the UI is not blocked indefinitely while
  the process continues.
- **What happens on app exit if the export is still owned after the wait budget?** The
  process releases export ownership and exits without hanging and without a hard
  "destroyed while still running" abort. The in-flight transcript may be incomplete or
  abandoned. Completeness is required only when ownership ends within the budget. This
  is not a general mid-write cancel feature; it is the shutdown abandon / orphan
  policy so exit can finish.
- **Why not defer disposal on exit the same way as tab close?** Deferral needs a living
  process. Exit cannot wait indefinitely (NFR) and this task does not add interruptible
  mid-write cancel UX. After the bounded exit budget, releasing ownership so exit
  proceeds is the required business outcome.
- **Does this change export formats or menus?** No. Open-tab export behavior stays the
  same; only close and exit teardown/disposal (and exit abandon after budget) change.
- **Are synthetic closeEvent-only tests enough?** No. DoD requires regression through
  real tab-removal and app-exit paths.
- **Who accepts the requirements?** The autonomous sprint orchestrator after
  independent review PASS; Step 1 stays `[/]` until that gate marks `[x]`.
