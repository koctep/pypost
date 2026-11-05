# PYPOST-1324: Make connected-library import work interruptible

## Goals

When collection import teardown stops an in-flight connected-library operation, that
library work must observe a cooperative cancellation request and stop at a safe
checkpoint so teardown can finish with a short, bounded final wait. Today a stuck
library operation can only be joined: it consumes the whole remaining teardown
budget and is then abandoned while still running. That is the worst-case shutdown
delay for collection import.

The business reason is follow-up 3 of
[PYPOST-1264 technical debt](../PYPOST-1264/60-tech-debt.md) (design Risk 4 /
performance concern: the library worker cannot be interrupted). PYPOST-1264 made
collection-import teardown budgeted and interruptible for file-parse work, but
connected-library work remains join-only. Users and maintainers therefore still lose
bounded, clean release when library listing or candidate resolution stalls during
teardown or cancel.

## User Stories

- As a user cancelling or closing during a connected-library collection import, I
  want that library work to stop cooperatively so teardown does not burn the entire
  remaining wait budget and leave a running library operation behind.
- As a user whose connected-library import completes normally (no cancel or
  teardown), I want listing, candidate resolution, success, and failure outcomes
  to behave as they do today.
- As a user or operator of other Library Manager flows that share the same
  background library-operation runner (library UI and MCP library source picking),
  I want those flows to keep working, and where they already stop or tear down
  work, to be able to request the same cooperative stop without forcible kill.
- As a maintainer, I want automated proof that a stuck or long-running library
  operation observes cancellation during teardown and that the final wait stays
  within a documented short bound when interruption is honored, instead of always
  consuming the full remaining budget.

## Definition of Done

1. **Cooperative stop for connected-library work.** An active connected-library
   collection import or refresh that runs as background library-operation work
   observes a cooperative cancellation request and stops at a safe checkpoint.
   Blocking library discovery (entry listing) and candidate resolution must not
   ignore cancellation for the whole operation.
2. **Teardown uses interruption then a bounded final wait.** Collection-import
   teardown requests cooperative interruption of an in-flight library operation
   and then waits only within a short, documented final-join bound (subject to
   the remaining caller budget from PYPOST-1264), rather than always joining for
   the entire remaining budget with no prior stop request.
3. **Clean vs unclean outcomes preserved.** When the library operation stops
   within that bounded wait, teardown can report a clean release for that work.
   When it does not stop in time, teardown still returns unclean within the
   caller budget and must not hang indefinitely. No forcible thread kill.
4. **No late library results after teardown.** After teardown has disconnected
   and released the library operation, success or failure outcomes from that
   operation must not reach the collections UI or change collections.
5. **Non-cancelled library work unchanged.** Successful listing/resolution,
   reported failures, and progress for library operations that are not cancelled
   retain existing observable behavior.
6. **Shared consumers remain safe.** Other callers that use the same background
   library-operation runner (library presenter flows and MCP library source
   picking) continue to run successful and failed operations correctly. Any
   cancel or teardown path those callers already have may request cooperative
   interruption; this task does not require redesigning their product workflows.
7. **Regression coverage.** Automated tests demonstrate that an in-flight library
   operation observes cooperative cancellation during collection-import teardown
   and that the final wait is bounded when interruption is honored. Coverage
   accounts for the shared runner and for timing-sensitive reproduction of a
   stuck or long-running library operation. Tests use explicit timeouts and
   bounded waits.
8. Repository gates run through `make` targets; no new failures are attributable
   to this task.

## Task Description

### Problem

Collection import runs connected-library listing and candidate resolution as
background library-operation work. File-parse import already supports cooperative
cancellation during teardown. The library path does not: teardown can only wait
for the library operation to finish. If that work is stuck or slow, it consumes
whatever teardown budget remains (up to the default collections share), returns
unclean, and abandons a still-running operation. PYPOST-1264 documented this as
Risk 4 and deferred interruptibility to this follow-up.

### Business reason

Users expect cancel and close to stop background import work in a bounded,
predictable way. Join-only library work undermines that contract and creates the
worst-case collection-import shutdown delay. Maintainers need the same
cooperative-stop guarantee for library import that file import already has, plus
regression proof that a long-running library operation can be stopped within a
short final wait.

### Implementation language

Python.

### Scope

- Cooperative cancellation for background library-operation work used by
  connected-library collection import and refresh, including discovery/listing
  and candidate-resolution phases that can block.
- Collection-import teardown requests that stop and uses a bounded final wait
  for the library operation (within the existing PYPOST-1264 budget contract).
- Safety for other consumers of the same background library-operation runner
  (library UI and MCP library source picking): no regressions on normal
  success/failure; cancel/teardown paths may use cooperative interruption where
  they already stop work.
- Automated regression for interruptible library work during collection-import
  teardown, including a timing-sensitive stuck/long-running scenario.

### Out of scope

- Registering collections with main-window shutdown (PYPOST-1321) and naming the
  application-wide shutdown budget (PYPOST-1325).
- Broader cancellation lifecycle matrices and reader contracts (PYPOST-1265,
  PYPOST-1266); streaming/decoding responsiveness (PYPOST-1267).
- Consolidating unrelated worker-finish wait constants (PYPOST-1323).
- Changing import planning, conflict resolution, collection application, or
  Library Manager product workflows beyond enabling cooperative stop of shared
  background library operations.
- Forcible termination of background threads.
- Guaranteeing immediate stop inside a single uninterruptible OS or network
  call; cancellation is cooperative at safe checkpoints.

### Non-functional requirements

- No forcible termination of library or other import work; interruption stays
  cooperative.
- Collection-import teardown remains bounded by the caller budget; a stuck
  library operation must not force waiting beyond that budget.
- When interruption is honored, the final library join after the stop request is
  short and documented, not “whatever budget remains.”
- No added delay when no library operation is active.
- Diagnostics must not expose library entry content or secrets.
- Automated checks remain deterministic with explicit timeouts and bounded waits.

### Constraints and assumptions

- File-parse import already has cooperative interruption; this task closes the
  connected-library gap identified as PYPOST-1264 Risk 4.
- Collection-import teardown already honors a shared deadline and a short
  final-join concept for the file worker; library work should align with that
  interrupt-then-bounded-join pattern at the requirements level without
  prescribing how it is implemented.
- Library discovery/listing and candidate resolution today have no cancellation
  observation points; reaching those blocking phases with a cancel signal is
  required for DoD 1.
- The background library-operation runner is shared across collection import,
  the library presenter, and MCP library source picking; interruptibility must
  not break those consumers’ normal operation.
- Waits are not hard real-time guarantees under OS stalls or resource
  exhaustion.
- Timing-sensitive reproduction is expected; tests must still use explicit
  timeouts and bounded waits per project testing rules.

## Main Entities

- **Connected-library import work**: background listing of library entries and
  resolution of selected candidates into importable collections.
- **Background library-operation runner**: the shared one-shot background runner
  used for Library Manager service operations (collection import, library UI,
  MCP library source picking).
- **Cooperative cancellation request**: a stop signal that in-flight library
  work observes at a safe checkpoint without forcible kill.
- **Safe checkpoint**: a point during listing or candidate resolution where work
  may stop further progress after seeing cancellation.
- **Collection-import teardown**: stopping, waiting for, disconnecting, and
  releasing import work within a caller time budget without delivering late
  results to the UI.
- **Bounded final wait**: the short, documented join after a cooperative stop
  request (capped by remaining budget) used instead of joining for the entire
  remaining budget with no stop request.
- **Teardown result**: clean when library (and other) import work stopped and
  was released within budget; unclean otherwise.
- **Shared consumer**: another UI or MCP flow that uses the same background
  library-operation runner and must keep working for normal success and failure.

## Q&A

This is an autonomous run (sprint-task-runner); clarifying questions were
resolved from the Jira issue, PYPOST-1264 debt/requirements/architecture Risk 4,
and related tickets rather than left open.

- **Why is this needed?** Connected-library import teardown is join-only. A stuck
  library operation consumes the remaining budget and is abandoned running
  (PYPOST-1264 Risk 4 / follow-up 3). Users lose bounded cancel/close behavior;
  maintainers lack interruptibility parity with file-parse import.
- **Is the business goal only collection-import teardown?** The primary user-facing
  gap is collection-import teardown and cancel during connected-library import.
  Because the runner is shared, interruptibility must remain safe for library UI
  and MCP source picking; redesigning those product flows is out of scope.
- **Must listing and candidate resolution both observe cancellation?** Yes. Those
  are the blocking phases called out in the issue estimate; otherwise a stop
  request cannot affect a stuck library import.
- **Does “bounded final wait” replace the overall teardown budget?** No. The
  overall caller budget from PYPOST-1264 remains. After requesting stop, the
  final library join should be a short documented bound capped by what budget
  remains, not an unconditional full-budget join with no stop request.
- **Is forcible kill allowed if the operation ignores cancellation?** No.
  Unclean teardown within budget remains the outcome when cooperative stop is
  not honored in time.
- **Who accepts the requirements?** The autonomous sprint orchestrator after
  independent review.
