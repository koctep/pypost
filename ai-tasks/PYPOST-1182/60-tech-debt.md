# PYPOST-1182: Technical Debt Analysis

## Shortcuts Taken

- **Synchronous Event Loop Draining Loop**: `CollectionImportActions.wait_idle()` uses a polling loop with `QApplication.instance().processEvents()` and `QElapsedTimer` to drain in-flight worker signals on the main thread. While standard for deterministic Qt UI test execution, production UI lifecycle management typically benefits from fully asynchronous promise/future or signal-slot decoupling.
- **Fixed Default Timeout**: Default wait timeout of 5000ms (`timeout_ms=5000`) is hardcoded as a default parameter across `wait_idle()` and `wait_import_idle()`. While conservative and sufficient for fast test execution and standard collection files, very large import archives on constrained CI runners may require environment-configurable timeouts.

## Code Quality Issues

- **Multiple State Flags vs. Explicit State Machine**: `CollectionImportActions` tracks in-flight work via multiple distinct attributes (`self._is_preparing`, `self._worker`, `self._button`). Refactoring these state variables into an explicit lifecycle state enum (e.g. `CollectionImportState: IDLE, PREPARING, PARSING, APPLYING`) would reduce state coordination complexity and make edge-case transitions easier to verify.
- **Presenter Test Helper Coupling**: In `tests/test_collections_import_ui.py`, `_wait_import(done, presenter=None)` accepts an optional presenter argument. Making `presenter` mandatory or extracting `_wait_import` into a shared Qt UI presenter test helper module (e.g. in `tests/helpers/`) would standardize event loop draining across all presenter test suites.

## Missing Tests

- **Concurrent Import Invocations**: When `is_busy()` is `True`, subsequent calls to `import_collections()` return early to prevent concurrent parse workers. Additional test coverage simulating rapid-fire GUI button triggers or simultaneous shortcut keystrokes would further validate UI lock-out behavior.
- **Worker Cancellation on Early Teardown**: Tests currently verify that `wait_idle()` waits for the background worker to finish and join before panel destruction. Tests for immediate worker interruption/cancellation (e.g., via `requestInterruption()`) during long parse operations on widget close do not yet exist.

## Performance Concerns

- **Event Loop Polling in Tight Loop**: In `CollectionImportActions.wait_idle()`, calling `QApplication.processEvents()` inside a while loop with `QElapsedTimer` can cause brief CPU spinning if no pending Qt events exist while waiting for the worker thread. If `wait_idle()` is ever invoked outside of testing/teardown contexts, adding a bounded yield (e.g. `QThread.msleep(1)` or event-driven semaphores) would minimize CPU load.

## Follow-up Tasks

- `NON-BLOCKER — tech debt`: Refactor `CollectionImportActions` internal state flags into a formalized `CollectionImportState` enum state machine. Jira: [PYPOST-1228](https://pypost.atlassian.net/browse/PYPOST-1228)
- `NON-BLOCKER — tech debt`: Implement cooperative worker thread cancellation (`QThread.requestInterruption()`) for `CollectionImportWorker` to allow immediate abort upon panel closure. Jira: [PYPOST-1229](https://pypost.atlassian.net/browse/PYPOST-1229)
- `NON-BLOCKER — tech debt`: Extract `_wait_import` presenter lifecycle draining logic into `tests/helpers/` for reuse across presenter test suites. Jira: [PYPOST-1230](https://pypost.atlassian.net/browse/PYPOST-1230)
- `NON-BLOCKER — pre-existing`: `tests/test_makefile.py::TestTargetExecution::test_test_succeeds_from_bare_venv_via_venv_test` timeout under high parallel test worker load.
- `NON-BLOCKER — pre-existing`: Baseline typing discrepancies reported during `make typecheck` in unrelated modules (`pypost/ui/dialogs/library_dialogs.py`, `pypost/ui/presenters/tabs_presenter.py`, `pypost/ui/widgets/mcp_client/mcp_client_tab.py`, `pypost/core/environment_variables_adapter.py`).
