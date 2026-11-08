# PYPOST-1453: Adaptive Join on Dialog Worker Teardown

## Goals

In PyPost, users interact with the Import Collection Variables dialog to preview,
select, and import environment variables from remote library collections and catalogs.
Because discovery and network fetching are asynchronous operations, background workers
execute on dedicated worker threads to prevent stalling the user interface during
network I/O.

When a user closes, cancels, or accepts the import dialog--or when switching collections
or presets while a prior fetch or catalog discovery is in-flight--the dialog teardown
routines terminate the active workers. Previously, dialog teardown relied on rigid,
hardcoded one-second synchronous joins (`wait(1000)`). While cooperative cancellation
tokens introduced in PYPOST-1425 allow background tasks to abort within milliseconds,
hardcoded 1000ms blocking joins create significant operational and experiential
shortcomings:

1. **Perceptible UI Freezes and Desktop Stutter**: A synchronous 1000ms wait blocks the
   Qt main event loop. If a worker takes even slightly longer than instantaneous return
   or if both discovery and fetch workers are sequentially torn down, the user interface
   visibly freezes. Clicking "Cancel", pressing "Escape", or clicking the window close
   button should feel instantaneous; delaying dialog dismissal by up to a full second
   degrades desktop responsiveness, violates user expectations, and risks triggering
   operating system "application not responding" (ANR) warnings.
2. **Duplicated and Fragmented Teardown Logic**: Teardown logic is duplicated across
   multiple dialog lifecycle methods (`reject`, `closeEvent`, `accept`, and internal
   cancellation callbacks) with hand-rolled worker checks and fixed timeouts, lacking
   a centralized, robust worker cancellation and cleanup pattern.
3. **Thread Model Divergence and Inflexibility**: PyPost recently introduced an adaptive
   polling join mechanism (`adaptive_thread_join`) with geometric backoff, progressive
   drain logging, and deadline enforcement for standard worker threads. However, Qt worker
   threads use a different interface, and the dialog teardown does not yet leverage
   adaptive polling. If workers exit in 5ms, the system should acknowledge termination
   within milliseconds rather than waiting through fixed, unobservable intervals.

The business goal of this task is to replace all rigid 1000ms worker join timeouts in
the Import Collection Variables dialog with an adaptive thread join mechanism supporting
both Qt worker threads and standard thread objects. This ensures immediate UI unblocking
upon cancellation, prevents modal dialog freezes, bounds teardown time under failure
conditions, provides observability into worker drain times, and centralizes worker
lifecycle teardown across the dialog.

## Programming Language

- **Implementation language**: Python

## User Stories

- As an **API Workspace Operator / Desktop User**, when I close, cancel, or accept the
  Import Collection Variables dialog while a background catalog discovery or collection
  fetch is running, I want the dialog to dismiss immediately without UI lag or modal
  dialog freezing, so that my desktop experience remains smooth and responsive.
- As an **Interactive User switching collections or presets**, when I select a different
  collection or preset in the dialog while a fetch or discovery operation is still active,
  I want the superseded worker to be cancelled and torn down quickly without stuttering
  the UI controls.
- As an **Automated Test Runner / CI Pipeline**, when test suites exercise dialog
  opening, cancellation, and closure across hundreds of test cases, I want worker
  teardowns to resolve adaptively in milliseconds rather than incurring cumulative
  1000ms blocking sleeps, dramatically speeding up test execution and preventing flaky
  thread leak warnings.
- As a **PyPost Maintainer / Developer**, when background workers are torn down or fail
  to terminate cleanly, I want clear, structured diagnostic logs detailing elapsed drain
  times and timeout warnings, and I want a consistent, centralized helper pattern across
  dialog teardown points rather than duplicated hand-rolled wait calls.

## Definition of Done

This task is considered complete when:
1. All hardcoded synchronous `wait(1000)` calls on worker teardown in
   `ImportCollectionVariablesDialog` (across discovery worker cancellation, fetch
   worker cancellation, `reject()`, `closeEvent()`, and `accept()`) are eliminated and
   replaced with adaptive thread joining.
2. The adaptive thread joining mechanism polymorphically handles both standard Python
   threads and Qt worker threads (supporting duck-typed thread interfaces for liveness
   checking and join/wait operations).
3. A centralized cancellation and teardown helper is introduced and utilized across all
   dialog teardown paths, ensuring consistent cancellation signaling, adaptive joining,
   diagnostic logging, and reference cleanup.
4. When a cancelled worker terminates quickly (for example, in under 10ms), dialog
   teardown returns immediately with low latency (under 50ms) without waiting for the
   full timeout ceiling.
5. A deterministic, bounded deadline (defaulting to 1.0s or configurable policy) is
   strictly enforced so that teardown never deadlocks or hangs the UI indefinitely if a
   worker is unresponsive.
6. Progressive backoff polling and drain diagnostics are emitted according to logging
   policy, recording elapsed drain duration and worker identity.
7. If a worker fails to exit before the timeout ceiling, a structured warning log is
   emitted, and the dialog gracefully completes teardown without crashing, throwing
   unhandled exceptions, or freezing the UI.
8. All edge cases (fast worker exit, stuck worker, None worker reference, already stopped
   worker, rapid consecutive cancel/re-open, and exceptions during teardown) are cleanly
   handled.
9. Backward compatibility is preserved for existing callers of the adaptive join
   utilities and existing dialog contracts.
10. Verification passes all project quality gates (`make check`, `make typecheck`, and
    `make verify-ai-tasks`).

## Task Description

### Problem Statement

During import operations in the `ImportCollectionVariablesDialog`, two distinct
background workers may execute asynchronously:
- `ManifestDiscoveryWorker`: Scans available library collections and manifests.
- `CollectionFetchWorker`: Fetches variable definitions and values from remote or local
  storage.

When the user dismisses the dialog via `reject()` (Cancel button or Escape key),
`closeEvent()` (window manager close button), or `accept()` (Import button), or when
a new fetch or discovery operation supersedes an active one, the dialog must ensure
that any active worker is stopped.

Currently, the dialog invokes `cancel()` followed by a blocking `wait(1000)` directly
on the worker. In Qt, calling `wait(1000)` on the main GUI thread halts all event loop
processing until either the worker thread finishes or the 1000ms deadline expires.
Even though cooperative cancellation aborts operations promptly, any delay or thread
scheduling jitter blocks the user interface. Furthermore, repetitive blocks of
`cancel()`, `wait(1000)`, and reference clearing are copy-pasted across multiple
methods.

PyPost needs a responsive, unified teardown workflow that:
- Slices wait times adaptively with progressive backoff, detecting thread completion
  with minimal latency.
- Seamlessly interoperates with both standard Python threads and Qt worker threads.
- Unifies worker cancellation, join, and reference clearing through a centralized helper.
- Bounds total teardown duration and logs diagnostic metrics for operational visibility.

### Functional Requirements

- **FR-1: Elimination of Rigid 1000ms Waits**:
  All instances of hardcoded `wait(1000)` on dialog worker instances must be replaced
  with adaptive thread join operations that check thread termination with low initial
  latency and progressive backoff.
- **FR-2: Polymorphic Worker Thread Support**:
  The adaptive join mechanism must transparently support:
  - Standard Python thread objects (exposing standard join and liveness check methods).
  - Qt worker thread objects (exposing Qt wait and running check methods).
  - Duck-typed thread doubles used in unit and integration testing.
- **FR-3: Centralized Cancellation and Teardown Helper**:
  The dialog must consolidate worker cancellation, adaptive joining, diagnostic
  logging, and reference cleanup (`worker = None`) into a centralized, reusable helper
  routine. Both discovery and fetch worker teardowns across `reject()`, `closeEvent()`,
  `accept()`, and internal supersession must delegate to this helper.
- **FR-4: Immediate Return on Inactive or Terminated Workers**:
  If a worker reference is `None`, or if the worker has already terminated before
  teardown begins, the teardown helper must return immediately without initiating
  polling slices or sleeping.
- **FR-5: Bounded Deadline Enforcement**:
  The teardown must enforce an upper deadline bound (e.g. 1.0 second maximum wait). If
  the worker does not terminate within this deadline, the helper must stop waiting, log
  an actionable warning, and allow the dialog to proceed with closing.
- **FR-6: Preservation of Dialog Lifecycle and State Contracts**:
  The dialog must continue to honor all existing Qt dialog contracts (`reject`, `accept`,
  `closeEvent`), generation discard tracking, selection models, and conflict resolution
  workflows.

### Non-Functional Requirements

- **NFR-1: Prompt UI Unblocking & Latency**:
  In nominal scenarios where workers exit within 10ms of cancellation, dialog teardown
  must complete in under 50ms, eliminating perceptible UI hesitation or lag.
- **NFR-2: Strict Deadline Bounds**:
  Total elapsed wait time during teardown must never exceed the configured maximum
  deadline, preventing indefinite application hangs or unresponsiveness.
- **NFR-3: Observability and Structured Logging**:
  Worker teardown must provide transparent operational observability:
  - Debug logs for initial poll slices and successful completion with elapsed duration.
  - Periodic drain notices if worker termination takes longer than intermediate
    threshold intervals.
  - Explicit warning diagnostics if a worker fails to exit within the maximum deadline,
    including worker name, elapsed time, and thread state.
- **NFR-4: UI Responsiveness and Non-Starvation**:
  Adaptive polling slices must balance fast reaction time with CPU efficiency, avoiding
  excessive busy-waiting.
- **NFR-5: Memory and Resource Cleanliness**:
  Worker references held by the dialog must be promptly cleared to allow garbage
  collection and release underlying resources.

### Scope Boundaries

- **In-Scope**:
  - Replacing fixed `wait(1000)` calls with adaptive join in
    `ImportCollectionVariablesDialog` (`_cancel_discovery_worker`, fetch worker
    cancellation, `reject`, `closeEvent`, and `accept`).
  - Extending adaptive join capabilities to polymorphically support Qt worker threads,
    standard threads, and duck-typed thread objects.
  - Implementing a centralized worker teardown helper in the dialog.
  - Adding comprehensive automated repro and unit tests verifying fast return latency,
    bounded timeout handling, polymorphic thread support, and diagnostic logging.
  - Updating task progress and developer documentation.
- **Out-of-Scope**:
  - Altering low-level HTTP/socket transport abort mechanisms (completed in PYPOST-1425).
  - Modifying other unrelated dialogs or windows across PyPost.
  - Changing variable parsing, conflict resolution, or environment persistence logic.
  - Rewriting Qt threading architectures or replacing Qt worker inheritance.

### Edge Cases

- **EC-1: Fast Worker Exit**:
  Worker detects cancellation token abort and terminates within 1-5ms. Adaptive join
  detects termination on the first poll slice and returns immediately (<10ms elapsed).
- **EC-2: Stuck or Blocked Worker**:
  Worker is blocked in an un-abortable operating system call or slow third-party library
  routine. Adaptive join polls up to the 1.0-second deadline, records a structured
  warning log, and returns without hanging the UI indefinitely.
- **EC-3: None Worker Reference**:
  Teardown is invoked when no worker was active (e.g., dialog opened and immediately
  closed before any action was taken). The helper handles the `None` reference cleanly
  as a no-op.
- **EC-4: Worker Already Completed**:
  Worker completed its operation normally before the user triggered cancel or close.
  Liveness check returns false immediately, and teardown finishes with 0ms delay.
- **EC-5: Rapid Successive Cancellations / Re-opens**:
  The user rapidly triggers cancel, re-opens the dialog, or quickly changes selections
  in dropdowns. Repeated calls to teardown must be idempotent, safe against race
  conditions, and never raise exceptions.
- **EC-6: Exception Safety During Teardown**:
  If an unexpected exception occurs while signalling or waiting on a worker, the
  teardown logic must catch or manage it safely so that the dialog dismissal is not
  blocked and the UI does not crash.

### Backward Compatibility Rules

- Existing callers of `adaptive_thread_join` (such as MCP server management) must
  continue to function with unchanged behavior and interface signatures.
- All public dialog methods (`reject`, `accept`, `closeEvent`) must retain their standard
  Qt method signatures and event handling behaviors.
- Existing unit tests for `ImportCollectionVariablesDialog` must continue to pass without
  regression.

## Q&A

**Q: Why is a 1000ms wait problematic if the dialog is closing anyway?**  
A: In desktop applications, users expect dialog closure upon clicking "Cancel" or
pressing "Escape" to happen instantaneously. A 1000ms synchronous block on the main GUI
thread freezes the entire application window, prevents OS window events from
processing, feels sluggish, and can cause the operating system to display an
"Application Not Responding" spinner. Furthermore, if both discovery and fetch workers
are tearing down, sequential 1000ms waits could freeze the UI for up to two full
seconds.

**Q: Why not just call worker.terminate()?**  
A: Forcing thread termination via `QThread.terminate()` is unsafe in Qt and Python
because it abruptly halts execution without releasing locks, freeing resources, or
executing `finally` blocks, leading to deadlocks or corrupted heap states. Clean
cooperative cancellation paired with adaptive joining allows the worker to cleanly shut
down while the main thread waits only as long as strictly necessary.

**Q: What thread types must be supported by the adaptive join mechanism?**  
A: It must polymorphically support standard Python `threading.Thread` instances (using
`join` and `is_alive`), Qt `QThread` instances (using `wait` and `isRunning`), and test
doubles or duck-typed thread objects implementing either interface.

**Q: Where should the centralized teardown helper reside?**  
A: The helper will be encapsulated within the dialog (or shared utility module if
appropriate) to standardize the sequence of requesting cancellation, running the
adaptive join within bounded limits, logging diagnostics, and clearing worker
references to `None`.
