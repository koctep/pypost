# PYPOST-1415: Technical Debt Analysis

## Shortcuts Taken

1. **Synchronous Connection and Manifest Discovery During Dialog Initialization**:
   - In [`ImportCollectionVariablesDialog.__init__`](file:///home/src/pypost/ui/dialogs/import_collection_variables_dialog.py#L892-L910), populating the collection dropdown (`self.collection_combo`) invokes `self.library_service.list_connections()` and `self.library_service.list_manifest_collections(conn.stable_id)` synchronously directly on the Qt main GUI thread.
   - While actual collection fetching is now asynchronously offloaded to `CollectionFetchWorker(QThread)` with non-blocking UI and cancellation, discovering available library connections and parsing remote catalog manifests upon dialog startup still occurs synchronously. If a remote library service experiences slow DNS, high network latency, or cold-start connection delay, opening the dialog may hesitate before rendering.
2. **Backward-Compatibility Facade for Legacy Table Item and Widget Inspection**:
   - To prevent breaking existing test suites (e.g. `tests/test_workspace_environment_import_diff_repro.py`) and legacy callers expecting `QTableWidget` semantics, [`CollectionVariablesTableView`](file:///home/src/pypost/ui/dialogs/import_collection_variables_dialog.py#L567-L674) implements a synthetic emulation facade:
     - [`TableItemProxy`](file:///home/src/pypost/ui/dialogs/import_collection_variables_dialog.py#L111-L148) proxies `item(row, col).text()`, `setText()`, `checkState()`, and `setCheckState()` back to the virtualized model.
     - [`HeaderItemProxy`](file:///home/src/pypost/ui/dialogs/import_collection_variables_dialog.py#L101-L109) proxies `horizontalHeaderItem(col).text()`.
     - `cellWidget(row, COL_STRATEGY)` dynamically instantiates and caches off-screen `QComboBox` instances in `self._strategy_combos`, bidirectionally synchronizing index changes with `model.setData()`.
   - While this achieved seamless backward compatibility with zero regressions, it introduces dual mutation pathways (real UI editing via `ConflictStrategyDelegate` vs. programmatic testing via synthetic `cellWidget` proxies) and stores proxy references in memory dictionaries (`_proxies` and `_strategy_combos`).
3. **Generation Counter Discard Rather Than Socket-Level Abort**:
   - In [`CollectionFetchWorker.cancel`](file:///home/src/pypost/ui/dialogs/import_collection_variables_dialog.py#L697-L705), cancellation sets `self._cancelled = True` and calls `self.requestInterruption()`.
   - However, standard synchronous socket / HTTP I/O in `library_service.read_collection()` does not automatically interrupt or abort blocked network socket reads when `requestInterruption()` is set. The background worker continues running until the remote socket read finishes or times out; the UI merely ignores the result because `_fetch_generation` was incremented. A full low-level cancellation would require an `AbortController` or explicit socket shutdown.
4. **Synchronous In-Memory Preset Profile Recalculation**:
   - In [`_on_preset_changed`](file:///home/src/pypost/ui/dialogs/import_collection_variables_dialog.py#L918) and [`CollectionVariablesTableModel.update_preset`](file:///home/src/pypost/ui/dialogs/import_collection_variables_dialog.py#L460-L490), switching between preset configuration profiles synchronously iterates over all records on the GUI thread to re-evaluate candidate values and status labels. While sub-5ms for 1,000–2,000 rows, this remains an $O(N)$ operation on the main event loop.

## Code Quality Issues

1. **Monolithic Module Violating Single Responsibility Principle**:
   - [`pypost/ui/dialogs/import_collection_variables_dialog.py`](file:///home/src/pypost/ui/dialogs/import_collection_variables_dialog.py) currently encompasses 1,301 lines of code containing 7 distinct components:
     - `CollectionVariableRowRecord` (data transfer entity)
     - `HeaderItemProxy` and `TableItemProxy` (backward-compatibility proxies)
     - `CollectionVariablesTableModel` (Qt model logic, secret masking, selection, bulk updates)
     - `ConflictStrategyDelegate` (Qt item delegate, on-demand combo editor)
     - `CollectionVariablesTableView` (Qt view subclass with proxy facade)
     - `CollectionFetchWorker` (Qt background worker thread with generation tracking)
     - `ImportCollectionVariablesDialog` (dialog widget, UI layout, action coordinators, domain dispatch)
   - Combining model, delegate, worker, view, and dialog logic into a single file makes the dialog module heavy. As recorded in the dialog LOC inventory (`ai-tasks/PYPOST-374/30-dialogs-audit-report.md`), this module should be refactored by extracting components into dedicated packages:
     - `pypost/ui/models/collection_variables_table_model.py`
     - `pypost/ui/delegates/conflict_strategy_delegate.py`
     - `pypost/ui/workers/collection_fetch_worker.py`
     - `pypost/ui/views/collection_variables_table_view.py`
2. **Coupling of Model to Concrete Domain Entities**:
   - `CollectionVariablesTableModel` directly receives and stores `target_environment: Environment` and inspects `target_environment.variables` and `target_environment.hidden_keys`. Decoupling the model into a pure presentation diff model that accepts generic diff records would make the model testable without domain mock objects.
3. **Hardcoded Column Indices and Constants**:
   - Column positions (`COL_SELECT = 0` to `COL_DESC = 8`) and column header strings are module-level constants. While clear, an `IntEnum` or column metadata registry would encapsulate column schema definitions cleanly.

## Missing Tests

1. **Network Partition and Mid-Stream Socket Termination**:
   - While [`tests/test_variable_import_virtualization_repro.py`](file:///home/src/tests/test_variable_import_virtualization_repro.py) tests clean `TimeoutError` and immediate failure recovery, tests simulating TCP dropouts, connection resets mid-payload transfer, SSL handshake aborts, or slow-drip partial responses (simulating flaky mobile or satellite connections) are not yet implemented.
2. **Malformed Manifest Streams and Corrupted Remote Payloads**:
   - Unit tests assume well-formed `Collection` objects or clean exceptions. Automated tests feeding truncated JSON, schema-violating manifests (e.g. non-string variable names or missing `variables` fields), or unhandled remote server errors into `read_collection` are missing.
3. **High-Frequency Concurrency and Dialog Lifecycle Churn**:
   - Stress tests simulating rapid user navigation (e.g. clicking 20 different remote collections in 500ms, or opening, canceling, and destroying dialogs in tight loops while background threads are actively running) to verify thread cleanup, signal disconnection, and garbage collection are not implemented.
4. **Accessibility and Assistive Technology Roles**:
   - Virtualized table cells and custom delegates do not currently implement explicit `Qt.ItemDataRole.AccessibleTextRole` or `Qt.AccessibleDescriptionRole` annotations, and no automated accessibility audits test screen reader compatibility for the table view.
5. **Test Timeout Compliance**:
   - All tests in `tests/test_variable_import_virtualization_repro.py` have explicit `@pytest.mark.timeout(30)` annotations and module-level `pytestmark = [pytest.mark.timeout(30)]`. There are zero missing timeout markers, fully satisfying the `do-testing` contract.

## Performance Concerns

1. **Memory Footprint for Massive 50,000+ Row Collections**:
   - The virtualized table model solves Qt visual widget allocation ($O(1)$ visual widgets in viewport). However, all variable records (`CollectionVariableRowRecord`) are retained in an in-memory Python list.
   - For collections containing 50,000 to 100,000 variables, the Python object graph (strings, records, dictionaries) consumes ~25–50 MB of memory. For extreme catalogs, a cursor-based or paged model (fetching variable chunks on demand as the user scrolls) would be required.
2. **JSON Deserialization and Object Instantiation on the GUI Thread**:
   - Although `read_collection` executes on `CollectionFetchWorker(QThread)`, the resulting deserialized `Collection` model is passed back to the main thread via Qt signals, where `_model.load_collection()` iterates over all items to instantiate `CollectionVariableRowRecord` objects. For 50,000+ variables, this loop consumes ~150–250ms of CPU time on the main UI thread during initial loading.
3. **Unbounded Proxy Cache Growth in Compatibility View**:
   - `CollectionVariablesTableView._proxies` caches `TableItemProxy` instances indefinitely for any accessed cell. If automated test suites or inspection scripts traverse every cell in a 10,000-row table via `.item(r, c)`, 90,000 proxy objects will be allocated and retained in memory until the dialog is closed.

## Follow-up Tasks

1. **Extract Virtualization Components into Dedicated Modules**:
   - Jira: [PYPOST-1423](https://pypost.atlassian.net/browse/PYPOST-1423)
   - Extract `CollectionVariablesTableModel`, `ConflictStrategyDelegate`, `CollectionVariablesTableView`, and `CollectionFetchWorker` from `pypost/ui/dialogs/import_collection_variables_dialog.py` into dedicated modules in `pypost/ui/models/`, `pypost/ui/delegates/`, `pypost/ui/views/`, and `pypost/ui/workers/`.
   - Target: Refactor `import_collection_variables_dialog.py` to under 500 lines of code.
2. **Asynchronous Connection and Remote Manifest Discovery**:
   - Jira: [PYPOST-1424](https://pypost.atlassian.net/browse/PYPOST-1424)
   - Offload `library_service.list_connections()` and `library_service.list_manifest_collections()` to a background startup worker or lazy loader so dialog initialization is instantaneous even on slow remote libraries.
3. **Low-Level Socket / HTTP Request Abort in `CollectionFetchWorker`**:
   - Jira: [PYPOST-1425](https://pypost.atlassian.net/browse/PYPOST-1425)
   - Introduce transport-level cancellation (e.g. closing socket handles or utilizing HTTP `AbortController`) so cancelled fetches do not consume network bandwidth or worker thread time.
4. **Fault-Injection Test Suite for Flaky Networks and Corrupted Manifests**:
   - Jira: [PYPOST-1426](https://pypost.atlassian.net/browse/PYPOST-1426)
   - Add automated test cases simulating network drops, TCP resets mid-stream, partial JSON manifests, and malformed variable schema payloads.
5. **Paged / Chunked Model Virtualization for Extreme Collections (50,000+ Variables)**:
   - Jira: [PYPOST-1427](https://pypost.atlassian.net/browse/PYPOST-1427)
   - Implement incremental chunking / cursor fetching in `CollectionVariablesTableModel` to support 50k–100k variable catalogs with sub-10MB memory overhead and instant initial load.
6. **`NON-BLOCKER — pre-existing`: Pre-existing lockfile drift in `requirements-dev.txt` causes `test_repro_check_lock_dev_detects_no_drift` failure**:
   - Jira: [PYPOST-1397](https://pypost.atlassian.net/browse/PYPOST-1397)
   - Test node: `tests/test_lockfile_verification.py::test_repro_check_lock_dev_detects_no_drift`
   - Description: `requirements-dev.txt` is stale relative to `requirements-dev.in` on the base commit, causing `make check-lock-dev` to fail during full test runs.
7. **`NON-BLOCKER — pre-existing`: Makefile test suites time out on shared base venv lock under full-suite parallel load**:
   - Jira: [PYPOST-1413](https://pypost.atlassian.net/browse/PYPOST-1413)
   - Test nodes:
     - `tests/test_makefile_target_install_test.py::TestTargetInstallTest::*`
     - `tests/test_makefile_target_filtering.py`
     - `tests/test_makefile_stamp_otel_idempotency.py`
     - `tests/test_makefile_stamp_test_idempotency.py`
     - `tests/test_makefile_install_stamp_contract.py`
   - Description: Heavy concurrent test execution leads to contention on virtual environment file locks, triggering worker timeouts.
