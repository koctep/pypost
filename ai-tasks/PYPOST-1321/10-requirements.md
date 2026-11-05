# PYPOST-1321: Register collection import teardown with main-window shutdown

## Goals

When a user closes the application while a collection import is running, that import work
must take part in the same coordinated, time-bounded shutdown that other main-window areas
already follow. Closing the app must interrupt and release in-flight collection import work
within a fair share of the overall shutdown wait budget, and must not leave background import
work running without any shutdown participation.

The business reason is follow-up 1 of
[PYPOST-1264 technical debt](../PYPOST-1264/60-tech-debt.md) (design Risk 5). PYPOST-1264
named and budgeted how collection import is stopped and released when its own teardown is
invoked, but application close never includes collections among the participants that share
the main-window shutdown deadline. Users therefore get orderly shutdown for tabs, history,
and environment work, while collection import workers are skipped on exit. Maintainers also
lack any automated proof that closing during file or library import stays within the shutdown
contract.

## User Stories

- As a user closing the application during a file-based collection import, I want shutdown to
  request interruption of that import, wait only within its share of the overall close budget,
  abandon the import without adding or changing collections, and finish the exit without
  hanging indefinitely.
- As a user closing the application during a connected-library collection import, I want the
  same bounded shutdown participation: the library import is waited for within the collections
  share of the budget and is released so results do not reach the UI after close starts.
- As a user closing the application when no collection import is running, I want no added
  delay from collections participation in shutdown.
- As a maintainer, I want collection import to be a first-class participant in main-window
  shutdown (including fencing that prevents new work after teardown has begun), with a clear
  share of the shared shutdown budget and a reportable outcome like other participants.
- As a maintainer, I want automated regression coverage that closing the app during an active
  file import and during an active library import exercises collections teardown under the
  shutdown budget.

## Definition of Done

1. **Collections participate in application close.** Closing the main window invokes
   collection import teardown as part of the same coordinated shutdown that already covers
   the other main-window teardown participants. Collection import is no longer omitted from
   that participant list.
2. **Fair share of the shutdown budget.** Collections receive a time allocation drawn from
   the overall application shutdown wait budget, consistent with how other participants share
   that budget. Collection import teardown must honor the allocation it is given (within the
   existing collection-import budget contract from PYPOST-1264).
3. **Both import kinds are covered.** Shutdown participation applies when a file-parse import
   worker is active and when a connected-library import worker is active.
4. **Preserved import teardown outcomes.** Observable collection-import teardown behavior from
   PYPOST-1264 remains: cooperative interruption only (no forcible kill); idle close adds no
   measurable collections wait; after teardown, no import results, progress, completion,
   failure, or cancellation outcome reaches the UI; no collections are added or modified;
   workers are released; repeated teardown remains safe.
5. **Reportable shutdown outcome.** Collections' contribution to main-window shutdown reports
   success or failure and activity in the same form expected of other shutdown participants
   (outcome, active/pending activity, and correlation with the shutdown run), so the overall
   close result remains aggregable and diagnosable.
6. **Shutdown fencing.** Once application teardown has begun, collections respect the same
   begin-teardown fencing rules as other participants: no new import admission after fencing,
   and collections are ordered among owners according to the existing main-window shutdown
   ordering contract.
7. **Regression coverage.** Automated tests demonstrate application close while a file import
   (parse worker) is in flight and while a library import (library worker) is in flight, and
   show that collections teardown runs under its allocated budget in those scenarios. Tests
   use explicit timeouts and bounded waits.
8. **Optional related naming.** Naming the overall application shutdown budget (tracked
   separately as [PYPOST-1325](https://pypost.atlassian.net/browse/PYPOST-1325)) may be done
   in this task when it is needed to allocate and document the collections share clearly.
   Completing PYPOST-1325 fully is not mandatory if the collections share can be allocated
   from the existing shutdown budget without new naming; any remaining naming debt stays on
   PYPOST-1325.
9. Repository gates run through `make` targets; no new failures are attributable to this task.

## Task Description

### Problem

Collection import runs file parsing and connected-library operations in background work.
PYPOST-1264 made stopping and releasing that work a named, budgeted policy when collections
teardown is called. Application close already walks a list of main-window teardown
participants, fences new work, splits a shared wait budget across them, and aggregates their
outcomes. Collections are not on that list today, so closing the app never interrupts or joins
collection import workers under any shutdown budget. Direct callers (panel teardown, tests)
still get the budgeted path; real application exit does not.

### Business reason

Users expect closing the app to stop background work in a bounded, predictable way. Skipping
collections on exit leaves import workers outside that contract and weakens the value of the
PYPOST-1264 policy. Maintainers need shutdown to treat collection import like other UI areas
and need regression proof for close-during-import.

### Implementation language

Python.

### Scope

- Include collection import teardown in main-window / application close as a shutdown
  participant with a share of the overall wait budget.
- Align collections' shutdown reporting and begin-teardown fencing with the expectations of
  that coordinated close path.
- Automated regression for app close during file import and during library import.
- Optionally name the application-wide shutdown budget when required to give collections a
  clear, documented share (overlap with PYPOST-1325).

### Out of scope

- Making the library import worker cooperatively interruptible (PYPOST-1324); shutdown may
  still wait out the remaining collections allocation and return unclean if the library worker
  does not finish in time, consistent with current collection-import teardown.
- Broader cancellation lifecycle matrices and reader contracts (PYPOST-1265, PYPOST-1266).
- Consolidating unrelated worker-finish wait constants in other components (PYPOST-1323).
- Changing import planning, conflict resolution, collection application, or decoding
  responsiveness.
- Forcible termination of background threads.
- Reworking shutdown for participants that already take part correctly (tabs, history,
  environment), except as needed to admit collections and allocate the shared budget.

### Non-functional requirements

- Application shutdown remains bounded; collections must not make close hang indefinitely.
- No forcible termination of import work; interruption stays cooperative where supported.
- No added delay when no collection import is active.
- Diagnostics must not expose imported collection content.
- Collections' reported outcome must remain usable for aggregating the overall shutdown result.

### Constraints and assumptions

- Existing main-window shutdown already fences admission, orders participants, and splits a
  shared budget; this task extends that contract to collections rather than inventing a
  separate close path.
- Collection import teardown already honors a caller-supplied budget (PYPOST-1264); the gap is
  that application close never supplies that call with an allocated share.
- Collections' current teardown result shape may not match what the main-window shutdown loop
  expects from participants; bringing them into alignment (without prescribing how) is part of
  meeting DoD 5.
- Library import may still consume the full remaining collections allocation when it cannot be
  interrupted; that limitation remains accepted until PYPOST-1324.
- Measurements and waits are not hard real-time guarantees under OS stalls or resource
  exhaustion.

## Main Entities

- **Application shutdown**: the coordinated close of the main window that fences new work,
  waits within an overall budget, and aggregates participant outcomes.
- **Shutdown participant**: a main-window area whose teardown is invoked during application
  close (today includes areas such as tabs, history, and environment; this task adds
  collections / collection import).
- **Shutdown budget share**: the portion of the overall close wait time allocated to one
  participant for its teardown.
- **Collection import work**: active background file parsing or connected-library operation
  started from the collections area.
- **Collection import teardown**: stopping, waiting for, disconnecting, and releasing that
  import work within a time budget, without delivering late results to the UI.
- **Teardown outcome report**: the success/failure and activity summary a participant returns
  so the overall shutdown can be diagnosed and aggregated (including correlation with the
  shutdown run).
- **Begin-teardown fencing**: the rule that once close has started for a participant, new
  work is not admitted under that participant.

## Q&A

This is an autonomous run (sprint-task-runner); clarifying questions were resolved from the
Jira issue, PYPOST-1264 debt/requirements, and related tickets rather than left open.

- **Why is this needed?** Application close skips collection import teardown, so the
  budgeted interrupt-and-release policy from PYPOST-1264 never runs on real exit. Users lose
  bounded close-during-import behavior; maintainers have no regression for that gap (Risk 5).
- **Is naming the application shutdown budget required here?** Only when needed to allocate
  and document the collections share clearly. Full delivery of PYPOST-1325 is optional; the
  mandatory outcome is that collections receive and honor a fair share on close.
- **Does this make the library worker interruptible?** No. That remains PYPOST-1324. This
  task ensures library import is waited for and released under the collections shutdown share.
- **Must collections report the same outcome shape as other participants?** Yes (DoD 5). How
  that alignment is achieved is deferred to architecture; requirements only require a
  reportable, aggregable outcome consistent with the shutdown contract.
- **Who accepts the requirements?** The autonomous sprint orchestrator after independent
  review.
