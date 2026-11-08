# PYPOST-1497: Optional LibraryPresenter close-path cooperative cancel

## Goals

When a user closes the Library Manager dialog or tears down the library presenter while a background library operation (such as cloning, pulling, branch switching, or refreshing) is actively executing, the application must cooperatively signal those operations to stop rather than abandoning them to run indefinitely in the background.

The business reason originates from follow-up item TD-5 of [PYPOST-1324 technical debt](../PYPOST-1324/60-tech-debt.md) (accepted DoD 6 residual). PYPOST-1324 made connected-library collection import interruptible during teardown and added cooperative cancellation capabilities to background library workers. However, wiring those capabilities to the interactive Library Manager dialog and presenter was intentionally deferred. Today, closing the Library Manager panel abandons in-flight operations without requesting cancellation. This wastes network and CPU resources, risks holding Git repository file locks (e.g., `index.lock`), and leaves operation admission locks in an undefined state if workers are cancelled. Providing a clean, cooperative close path ensures the application remains responsive, releases resources promptly, and behaves predictably upon dialog dismissal and re-opening.

## Task Description

The Library Presenter coordinates library management activities with underlying services and manages asynchronous tasks executed in background worker threads. When users interact with the Library Manager dialog, long-running operations like repository cloning or remote pulls run in the background. Currently, when the dialog is dismissed or the presenter is torn down:
1. No cooperative cancellation request is dispatched to active workers.
2. If cancellation occurs, worker cancellation signals are not handled by the presenter, leaving operation admission locks unreleased and preventing subsequent operations.
3. Abandoned workers may continue processing and attempt to report results or failures to destroyed or disconnected views.

This task specifies the functional requirements, operational bounds, and definition of done for wiring cooperative cancellation on panel close and presenter teardown, handling cancellation signals, releasing admission locks, and preventing stale callbacks.

**Implementation Language**: Python.

## User Personas & User Stories

### Personas
- **Desktop Application User**: Interacts with the Library Manager interface to synchronize, clone, and configure collection libraries. Expects prompt UI responsiveness and that closing a window stops unnecessary background activity without leaving invisible tasks running or blocking subsequent actions.
- **UI & Core Maintainer**: Develops and integrates presenter components into views and dialogs. Expects clean lifecycle semantics, deterministic cleanup, and no resource or thread leaks during panel dismissal or application shutdown.

### User Stories
- As a user closing the Library Manager dialog while a slow Git pull or clone is in progress, I want the ongoing background operation to be cooperatively cancelled so system resources and network bandwidth are not wasted on work I no longer need.
- As a user reopening the Library Manager dialog after previously closing it mid-operation, I want the library management controls to be immediately available and not locked in an "operation in progress" state.
- As a user whose library operations complete normally while keeping the dialog open, I want all normal completions, errors, and status updates to function exactly as before without premature interruption.
- As a maintainer integrating or testing the Library Presenter, I want an explicit teardown and cancel lifecycle contract that safely interrupts active workers and releases internal tracking without throwing unhandled exceptions or crashing the UI thread.

## Use Cases

### UC-1: Dialog Closed Mid-Operation
- **Actor**: Desktop Application User.
- **Precondition**: An asynchronous operation (e.g., repository pull or remote refresh) is in flight.
- **Trigger**: User closes the Library Manager dialog (via window close button, Escape key, or Close action).
- **Flow**:
  1. Dialog close hook triggers the presenter teardown/cancellation path.
  2. The presenter requests cooperative cancellation on all active workers.
  3. Worker threads observe the cancellation request at the next cooperative checkpoint and terminate cleanly.
  4. The presenter clears admission tracking for the stopped operations.
  5. No late UI callbacks or error alerts are emitted for the closed dialog.

### UC-2: Normal Uninterrupted Operation
- **Actor**: Desktop Application User.
- **Precondition**: The Library Manager dialog is open and an operation is initiated.
- **Trigger**: The operation runs to normal completion without the dialog closing.
- **Flow**:
  1. The worker finishes its execution successfully or reports a normal domain failure.
  2. The presenter processes the result, updates cached statuses, and emits success or failure signals to the view.
  3. Admission locks are released normally.

### UC-3: Presenter Teardown in Non-Dialog Contexts
- **Actor**: UI or Core Maintainer / Test Harness.
- **Precondition**: A `LibraryPresenter` instance is instantiated in an automated test, workbench tab, or shell window.
- **Trigger**: Teardown or cleanup is explicitly invoked on the presenter.
- **Flow**:
  1. Presenter issues cooperative cancellation to any tracked in-flight workers.
  2. Internal worker collections and operation admission entries are cleared or marked cancelled.
  3. Teardown completes promptly without hanging.

### UC-4: Reopening Dialog After Cancellation
- **Actor**: Desktop Application User.
- **Precondition**: An operation was previously cancelled when closing the dialog in UC-1.
- **Trigger**: User re-opens the Library Manager dialog.
- **Flow**:
  1. Library Manager dialog and presenter initialize fresh status queries.
  2. Admission tracking reflects that no operations are currently in progress.
  3. User can immediately start a new operation on the same library without receiving a false "operation already in progress" error.

## Functional Requirements

- **FR-1: Bulk Cooperative Cancellation on Teardown/Close**: The library presenter must provide a teardown/close lifecycle capability that requests cooperative cancellation for all currently active background operations.
- **FR-2: Dialog Close Hook Integration**: The Library Manager dialog must wire its window close and dismissal event to invoke the presenter's teardown/close cancellation path, ensuring background operations do not outlive the dialog.
- **FR-3: Cooperative Cancellation Signal Handling & Admission Release**: When an active background library worker is cancelled and emits its cancellation signal, the presenter must receive this signal, release the operation admission lock for that library and operation tuple, and emit a cancellation signal for listeners.
- **FR-4: Targeted Operation Cancellation**: The presenter must support targeted cancellation of a specific in-flight operation for a specified library, allowing individual operations to be cancelled independently of bulk panel teardown.
- **FR-5: Suppression of Late Results After Cancellation**: Following a cancellation or teardown request, late completion results or unexpected error signals from cancelled workers must be suppressed and not propagate to UI views as successful results or error popups.
- **FR-6: Preserved Non-Cancelled Semantics**: All normal library management workflows (refreshing status, listing entries, checking dirty state, switching branches, cloning, pulling, committing, and pushing) must preserve their existing observable behavior, return values, signal emissions, and error handling when cancellation is not requested.

## Non-Functional Requirements

- **NFR-1: Bounded Teardown & Responsiveness**: Teardown and cancellation operations must return promptly and never block the main UI thread. Any optional wait or join for worker exit must be strictly bounded by a short timeout.
- **NFR-2: Strictly Cooperative Cancellation**: Thread interruption and cancellation must be strictly cooperative. Forcible thread termination (e.g., hard thread killing) is prohibited.
- **NFR-3: Idempotency & Lifecycle Safety**: Teardown and cancellation entry points must be idempotent. Calling teardown multiple times or cancelling an already completed/cancelled operation must be safe and raise no unhandled exceptions.
- **NFR-4: Observability & Diagnostics**: Teardown execution, targeted cancellations, and worker cancellation events must produce structured log messages at DEBUG or INFO level. Diagnostics must not expose sensitive credentials, personal access tokens, or private repository URLs.

## Edge Cases & Concurrency Hazards

- **EC-1: Worker Completion Racing with Cancellation**: If a worker finishes its operation right as cancellation or teardown is requested, the system must process the race gracefully without raising unhandled exceptions or corrupting admission state.
- **EC-2: Worker Stuck in Uninterruptible I/O**: If an underlying external process or socket call does not check cancellation tokens immediately, the teardown path must still return within its bounded timeframe without freezing the application. The worker will exit at the next checkpoint or upon process termination.
- **EC-3: Teardown With Zero Active Operations (Idle Close)**: Closing the dialog or tearing down the presenter when no background operations are running must execute immediately with zero latency and no side effects.
- **EC-4: Operation Failure Coinciding with Cancellation**: If an operation fails (e.g., network disconnect) while cancellation is requested, the outcome must be treated as cancelled rather than emitting user-facing failure alerts.
- **EC-5: Rapid Close-and-Reopen Lifecycle**: If a user closes the Library Manager dialog and immediately reopens it, the new session must not be blocked or polluted by residual admission state from previous cancelled operations.

## Constraints and Assumptions

- **Scope Boundary**: This task focuses specifically on `LibraryPresenter`, `LibraryOperationWorker` cancellation integration, and `LibraryManagerDialog` close lifecycle. It does not redesign the underlying Git service operations, collection import teardown policies (already completed in PYPOST-1324 / PYPOST-1264), or introduce new dialog UI buttons.
- **Cooperative Checkpoints**: Cancellation is effective at cooperative token checkpoints in worker execution; operations blocked in non-interruptible external system calls will terminate at the earliest cooperative check.
- **No Forcible Kill**: Qt threads are not killed via `terminate()`; cancellation is requested via token invalidation and Qt thread interruption request.

## Definition of Done (DOD)

1. **DOD-1: Teardown Lifecycle Method**: `LibraryPresenter` provides an explicit teardown/close method that cancels all in-flight workers.
2. **DOD-2: Targeted Cancel Method**: `LibraryPresenter` provides a method to cooperatively cancel a specific in-flight operation by library ID and operation name.
3. **DOD-3: Worker Cancellation Connected**: `LibraryPresenter` connects to the worker's `operation_cancelled` signal, releases admission state via `finish_operation`, and emits a corresponding presenter-level cancellation signal.
4. **DOD-4: Dialog Close Integration**: `LibraryManagerDialog` intercepts close/teardown events and invokes the presenter's teardown path.
5. **DOD-5: No Stale Result Propagation**: Cancelled operations do not emit late success or failure signals to views.
6. **DOD-6: Preserved Existing Behavior**: All existing non-cancelled operations (pull, clone, refresh, branch list, etc.) continue to work without regression.
7. **DOD-7: Automated Test Coverage**: Automated tests verify:
   - Clean idle teardown without delay.
   - Cooperative cancellation of single active worker.
   - Cooperative cancellation of multiple concurrent workers on close/teardown.
   - Proper admission state release on cancellation.
   - Idempotent multiple teardown calls.
   - All tests use bounded waits and explicit timeout markers (`pytestmark = pytest.mark.timeout(...)`).
8. **DOD-8: Quality Gate Verification**: All repository checks run via Makefile pass: `make check`, `make typecheck`, `make check-baseline-metrics`, and `make verify-ai-tasks`.

## Q&A

- **Why is this task needed?**
  In PYPOST-1324, `LibraryOperationWorker` gained cooperative cancellation for collection-import teardown, but the interactive Library Manager presenter was left as residual tech debt (TD-5). Closing the panel currently leaves background workers running blindly.
- **Does this require adding new Cancel buttons to the dialog UI?**
  No. This task covers wiring the existing close/teardown lifecycle to cooperatively cancel in-flight operations and supporting programmatic cancellation. User-facing cancel buttons are out of scope.
- **What happens if a worker is executing an external git CLI command?**
  Cancellation is cooperative. The worker checks its cancellation token and interruption status. If a command cannot be interrupted mid-flight, teardown still returns promptly without blocking the UI thread, and the worker terminates when the check point is hit.
- **Who verifies and approves these requirements?**
  The requirements are validated by an independent review subagent during Step 1 of the Top-Down workflow before proceeding to Step 2 architecture design.
