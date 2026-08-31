# PYPOST-1148: Fix make check pytest deadlock on full test suite execution

## Research

### Root Cause Analysis

When executing the test suite in batch mode (`make check` or `pytest tests/ -m "not slow"`), pytest executes thousands of tests within a single Python process and shared `QApplication` instance. During execution around [`tests/test_collection_import_async_gaps.py`](file:///home/src/tests/test_collection_import_async_gaps.py), pytest hangs indefinitely in a Linux futex wait (`futex_wait_queue`).

Investigation of the codebase revealed several converging factors that produce this deadlock:

1. **Unjoined QThread Worker upon Test Completion**:
   In [`tests/test_collection_import_async_gaps.py::test_unexpected_reader_exception_surfaces_invalid_dialog`](file:///home/src/tests/test_collection_import_async_gaps.py#L77-L101):
   ```python
   with caplog.at_level(logging.ERROR):
       presenter.import_collections()
       process_until(lambda: mock_invalid.call_count >= 1, timeout_ms=3000)
   ```
   When `_exploding_reader` raises a `RuntimeError`, [`CollectionImportParseWorker.run()`](file:///home/src/pypost/core/qt/collection_import_parse_worker.py#L55-L91) catches the exception and emits `self.parse_failed.emit(exc)`.
   On the main thread, `process_until` pumps `app.processEvents()`. As soon as `parse_failed` arrives, [`_on_parse_failed`](file:///home/src/pypost/ui/presenters/collection_import_actions.py#L158-L166) invokes `show_collection_import_invalid_file_error` (`mock_invalid`).
   Because `mock_invalid.call_count >= 1` becomes `True` immediately, `process_until` returns! The test assertions execute and the test function terminates.
   In `finally:`, the test only calls `presenter.panel.close()`, which merely closes the `QWidget` panel.
   The background `QThread` worker is still in the process of finishing execution, releasing the Python GIL, or emitting `finished`. The test never waited for the worker thread to finish or join.

2. **Premature `is_busy()` Fall-Through and Event Loop Queue Drain Gap**:
   In [`CollectionImportActions.is_busy()`](file:///home/src/pypost/ui/presenters/collection_import_actions.py#L84-L89):
   ```python
   def is_busy(self) -> bool:
       if self._preparing:
           return True
       return self._worker is not None and self._worker.isRunning()
   ```
   When `_on_parse_failed` runs, it sets `self._preparing = False`.
   As soon as the worker thread exits its Python `run()` method, `self._worker.isRunning()` drops to `False`.
   Consequently, `is_busy()` evaluates to `False` **before** the queued `worker.finished` signal has been dispatched on the main GUI thread event loop!
   In [`_on_worker_finished`](file:///home/src/pypost/ui/presenters/collection_import_actions.py#L167-L177):
   ```python
   def _on_worker_finished(self) -> None:
       finished = self._worker
       self._worker = None
       if finished is not None:
           finished.deleteLater()
           if not finished.wait(_WORKER_FINISH_WAIT_MS):
               ...
   ```
   Because `_on_worker_finished` is only invoked when the main thread pumps events for `finished`, exiting `process_until` early means `_on_worker_finished` has **not** executed, `self._worker` has **not** been cleared, `finished.wait()` has **not** run, and `finished.deleteLater()` has **not** been called.

3. **GIL Contention, C++ Destructor, and Futex Deadlock in Batch Execution**:
   In isolation, the single test passes in ~0.14s because Python process shutdown reaps all OS threads simultaneously.
   However, during a full batch run of 2,700+ tests:
   - When `test_unexpected_reader_exception_surfaces_invalid_dialog` exits, `presenter` goes out of scope.
   - When Python's garbage collector collects `CollectionImportActions` and the underlying `CollectionImportParseWorker` (a PySide6 `QThread` wrapper), the C++ destructor `QThread::~QThread()` is executed.
   - In Qt C++, `QThread::~QThread()` detects that the thread is terminating or active and calls `wait()`, executing a low-level `pthread_join` that sleeps on a Linux futex.
   - Concurrently, the exiting worker thread requires the Python GIL or Qt event dispatcher locks to complete its shutdown.
   - Since the main thread holds the Python GIL during garbage collection while waiting on the futex, a circular deadlock occurs:
     - Main thread: holding GIL, waiting in C-level `pthread_join`/futex for worker thread to exit.
     - Worker thread: waiting to acquire GIL / lock to complete thread exit.
   - Default signal-based timeouts (like `SIGALRM` in `pytest-timeout`) cannot interrupt an uncooperative C-level futex wait inside glibc pthreads, causing pytest to hang forever.

4. **Missing Teardown Contract in Presenters**:
   Neither [`CollectionsPresenter`](file:///home/src/pypost/ui/presenters/collections_presenter.py) nor [`CollectionImportActions`](file:///home/src/pypost/ui/presenters/collection_import_actions.py) provides an explicit `teardown()` method. Presenters rely on callers manually knowing to call `wait_import_idle()`, which tests in `test_collection_import_async_gaps.py` failed to do.

## Architecture

### Module Diagram

```mermaid
graph TD
    subgraph UI Layer
        CP[CollectionsPresenter]
        CIA[CollectionImportActions]
    end

    subgraph Core / Worker Layer
        CIPW[CollectionImportParseWorker <br/>(QThread)]
        RIF[ReadImportFile / Core Reader]
    end

    subgraph Test Harness
        TEST[test_collection_import_async_gaps.py]
        PU[process_until / wait_idle]
    end

    TEST -->|imports collection| CP
    CP -->|delegates import flow| CIA
    CIA -->|spawns on-thread start| CIPW
    CIPW -->|executes off-thread| RIF

    CIPW -.->|parse_failed / parse_completed| CIA
    CIPW -.->|finished signal (queued)| CIA

    TEST -->|synchronizes / drains| CP
    CP -->|wait_import_idle / teardown| CIA
    CIA -->|waits until _worker is None / joined| CIPW
```

### Module Responsibilities

| Module | Responsibility | Key Architectural Changes |
| --- | --- | --- |
| [`CollectionImportActions`](file:///home/src/pypost/ui/presenters/collection_import_actions.py) | Coordinates file selection, background worker execution, conflict resolution, and persistence. | 1. Update `is_busy()` to return `True` while `self._worker is not None` (preventing premature idle detection while worker teardown is pending).<br/>2. Update `wait_idle()` to loop until `self._worker is None` and pump event loop to process deferred deletes.<br/>3. Add `teardown(timeout_ms)` to boundedly wait/stop/clean up active workers before destruction. |
| [`CollectionsPresenter`](file:///home/src/pypost/ui/presenters/collections_presenter.py) | Owns the collections panel, tree actions, and delegates import/export. | Add `teardown()` method that invokes `_import_actions.teardown()` and closes the panel, exposing a consistent lifecycle contract for tests and parent widgets. |
| [`CollectionImportParseWorker`](file:///home/src/pypost/core/qt/collection_import_parse_worker.py) | Background `QThread` executing parsing off the main GUI thread. | Ensure clean signal emission order and safe thread termination. |
| [`tests/test_collection_import_async_gaps.py`](file:///home/src/tests/test_collection_import_async_gaps.py) | Regression and gap test suite for asynchronous collection import. | 1. Ensure all async tests (`test_unexpected_reader_exception_surfaces_invalid_dialog`, `test_status_bar_lifecycle_transitions`, `test_real_json_file_async_import_integration`) call `presenter.wait_import_idle()` to guarantee complete worker drain.<br/>2. In `finally:`, call `presenter.teardown()` instead of only `presenter.panel.close()`. |

### Architectural Patterns

1. **Active Object / Explicit Lifecycle Drain Pattern**:
   Background asynchronous workers (`QThread`) must have an explicit, bounded lifecycle state machine. A component is not idle merely because `isRunning()` has turned false; it is only idle once the worker instance has emitted `finished`, the main thread has reaped the object, native thread join has completed, and all queued meta-call events are cleared.
2. **Deterministic Teardown Guard (RAII / Context Cleanliness)**:
   Presenters that manage asynchronous threads or network controllers must provide an idempotent `teardown()` method. Test cases and parent containers invoke `teardown()` in `finally` blocks or fixture teardowns to guarantee that no running OS threads outlive the test scope.
3. **Event Loop Deferred Event Drainage**:
   After a `QThread` finishes and is marked for deletion via `deleteLater()`, the Qt event loop must be pumped (`app.processEvents()`) to process `QEvent::DeferredDelete` events while the test scope is active, preventing memory reclamation or futex waits during subsequent test setup or garbage collection.

### Interface & API Definitions

```python
class CollectionImportActions(QObject):
    def is_busy(self) -> bool:
        """Return True while worker parse or teardown is in flight.

        Busy condition: self._preparing or self._worker is not None.
        """
        ...

    def wait_idle(self, timeout_ms: int = 5000) -> bool:
        """Pump event loop and wait until background worker is completely finished and joined.

        Ensures _worker is reset to None and all deferred deletion events are processed.
        """
        ...

    def teardown(self, timeout_ms: int = 5000) -> None:
        """Idempotent teardown ensuring background worker is stopped, joined, and drained."""
        ...


class CollectionsPresenter(QObject):
    def wait_import_idle(self, timeout_ms: int = 5000) -> bool:
        """Delegates to self._import_actions.wait_idle(timeout_ms)."""
        ...

    def teardown(self) -> None:
        """Tears down import actions and presenter resources cleanly."""
        ...
```

## Implementation Plan

### Mandatory — Failing Repro (next Step 3)

- **Test Path**: `tests/test_collection_import_teardown_repro.py`
- **What it asserts**:
  1. **Interface Contract**: Asserts that `CollectionsPresenter` and `CollectionImportActions` expose a callable `teardown()` method.
  2. **Worker Drain upon Error**: Reproduces the reader exception scenario (`_exploding_reader`) where `parse_failed` triggers `show_collection_import_invalid_file_error`.
  3. **Busy State Retention during Worker Finalization**: Asserts that `presenter._import_actions.is_busy()` remains `True` after `mock_invalid` is called until the worker thread has completely finished, emitted `finished`, and been set to `None`.
  4. **Clean Teardown Guarantees**: Asserts that executing `presenter.teardown()` ensures `presenter._import_actions._worker is None` and that the thread is not left active or unjoined.
- **How to force failure on unpatched code**:
  On unpatched code:
  - `hasattr(presenter, "teardown")` evaluates to `False`, raising an `AssertionError`.
  - `hasattr(presenter._import_actions, "teardown")` evaluates to `False`, raising an `AssertionError`.
  - Immediately after `mock_invalid` is called, `is_busy()` returns `False` even though `_worker is not None`, demonstrating premature idle exit.
  - The worker remains in `presenter._import_actions._worker` without being joined when `presenter.panel.close()` is called.
- **Sequencing**:
  1. Step 2: Architecture design and verification (this document).
  2. Step 3: Implement `tests/test_collection_import_teardown_repro.py` and verify that it fails (`pytest` red test via `make test`).
  3. Step 4: Implement `is_busy()`, `wait_idle()`, `teardown()` in `CollectionImportActions` and `CollectionsPresenter`; update `tests/test_collection_import_async_gaps.py`; verify tests turn green.

### Step 4 Development Steps

1. **`pypost/ui/presenters/collection_import_actions.py`**:
   - Update `is_busy()`:
     ```python
     def is_busy(self) -> bool:
         return self._preparing or self._worker is not None
     ```
   - Update `wait_idle(timeout_ms: int = 5000) -> bool`:
     - Loop while `self.is_busy()`.
     - In the loop, check elapsed time against `timeout_ms`.
     - Pump `app.processEvents()` if `app` exists, or `self._worker.wait(10)`.
     - Once idle, perform an additional `app.processEvents()` to process deferred deletions.
   - Implement `teardown(timeout_ms: int = 5000) -> None`:
     - If `self.is_busy()`, call `self.wait_idle(timeout_ms)`.
     - If `self._worker is not None` and `self._worker.isRunning()`:
       - Request interruption / quit and wait boundedly.
     - Reset `self._worker = None` and `self._set_preparing(False)`.
     - Pump `app.processEvents()`.
2. **`pypost/ui/presenters/collections_presenter.py`**:
   - Implement `teardown() -> None`:
     - Call `self._import_actions.teardown()`.
     - Call `self._panel.close()`.
3. **`tests/test_collection_import_async_gaps.py`**:
   - In `test_unexpected_reader_exception_surfaces_invalid_dialog`:
     - Add `assert presenter.wait_import_idle()` to drain the worker thread after dialog assertion.
     - In `finally:`, call `presenter.teardown()`.
   - In `test_status_bar_lifecycle_transitions`:
     - Add `assert presenter.wait_import_idle()`.
     - In `finally:`, call `presenter.teardown()`.
   - In `test_real_json_file_async_import_integration`:
     - Add `assert presenter.wait_import_idle()`.
     - In `finally:`, call `presenter.teardown()`.
   - In `test_import_skipped_when_already_busy`:
     - In `finally:`, call `presenter.teardown()`.

## Q&A

**Q: Why did the deadlock occur only during full batch test runs and not in single-test isolation?**
A: In single-test isolation, the pytest process terminates immediately after the test, causing the operating system to forcibly reap all threads before any garbage collection cycle or futex wait can block. In a batch run of 2,700+ tests, pytest continues executing in the same process; subsequent test executions trigger Python garbage collection. When Python GC deallocates an unjoined `QThread` whose thread is still exiting, `~QThread()` invokes `pthread_join`, causing the main thread to block on a futex while holding the Python GIL.

**Q: Why didn't `pytest-timeout` signal-based timeout abort the hanging test?**
A: `pytest-timeout` uses `signal.setitimer(signal.ITIMER_REAL, ...)` by default to raise an exception on `SIGALRM`. However, when a thread is blocked in a C-level kernel futex wait (`futex_wait_queue`) inside glibc pthreads without returning to the Python interpreter loop, the Python signal handler cannot execute until the C call completes, rendering the signal-based timeout ineffective.

**Q: Does modifying `is_busy()` to check `self._worker is not None` cause any regressions in UI responsiveness?**
A: No. In normal operation, `_on_worker_finished` is invoked immediately after the worker finishes its `run()` method and the main event loop processes the `finished` signal (taking less than a millisecond). Keeping `is_busy() == True` during this brief window prevents race conditions where a second import could be triggered while the previous worker is still finalizing.

**Q: How does `presenter.teardown()` improve robustness for future tests?**
A: By establishing a clear `teardown()` contract on `CollectionsPresenter`, any test or widget harness can guarantee that background workers are stopped, joined, and that deferred deletions are processed before exiting the test scope, preventing asynchronous thread leaks across the entire suite.
