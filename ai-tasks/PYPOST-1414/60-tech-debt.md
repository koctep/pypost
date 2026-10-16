# PYPOST-1414: Technical Debt Analysis

## Shortcuts Taken

1. **`QTableWidget` Cell Widgets vs `QItemDelegate`**:
   - In [`ImportCollectionVariablesDialog._populate_variables_table`](file:///home/src/pypost/ui/dialogs/import_collection_variables_dialog.py#L340-L347), per-row conflict resolution dropdowns are instantiated as standalone `QComboBox` widgets and embedded via `self.vars_table.setCellWidget(i, COL_STRATEGY, combo)`. While this delivered full interactive combo selection with minimal code and no custom paint logic, instantiating separate `QWidget` instances inside table cells bypasses Qt's standard item delegate model (`QStyledItemDelegate`). This introduces additional widget hierarchy overhead and memory consumption compared to delegate-based rendering.
2. **Dynamic UI Cell Querying for Strategy and Selection State**:
   - Instead of maintaining an authoritative presentation model or state store, [`ImportCollectionVariablesDialog`](file:///home/src/pypost/ui/dialogs/import_collection_variables_dialog.py) extracts state on-demand by traversing rows and querying UI widgets via [`get_row_strategy`](file:///home/src/pypost/ui/dialogs/import_collection_variables_dialog.py#L374-L382), [`get_variable_conflict_strategies`](file:///home/src/pypost/ui/dialogs/import_collection_variables_dialog.py#L402-L411), and [`is_row_selected`](file:///home/src/pypost/ui/dialogs/import_collection_variables_dialog.py#L432-L441). While straightforward and safe for current collection sizes, reading back state directly from widget instances couples logic to UI representation.
3. **Preset Profile Switching In-Place Cell Updates**:
   - In [`_on_preset_changed`](file:///home/src/pypost/ui/dialogs/import_collection_variables_dialog.py#L249-L277), changing the active preset profile iterates over the existing rows and updates only `COL_CANDIDATE_VALUE` in order to preserve existing per-row combo selections. This avoids rebuilding the table, but relies on table rows remaining strictly aligned with collection variables. If collection profiles ever support variable re-ordering or dynamic variable introduction per preset, this localized cell patching would require redesign.
4. **Synchronous Library Collection Inspection on Main GUI Thread**:
   - In [`_get_selected_collection`](file:///home/src/pypost/ui/dialogs/import_collection_variables_dialog.py#L209-L230), reading external library collections via `self.library_service.read_collection(...)` is executed synchronously on the Qt main GUI thread during collection combo index changes and upon dialog acceptance. For local workspace collections this is instantaneous, but for remote manifests or slow network storage this could trigger brief UI frame drops.

## Code Quality Issues

1. **Dialog Presentation and Domain Workflow Coupling**:
   - [`ImportCollectionVariablesDialog`](file:///home/src/pypost/ui/dialogs/import_collection_variables_dialog.py) handles table layout, widget creation, bulk button actions, summary recounting, and direct domain invocation of [`import_collection_variables_to_environment`](file:///home/src/pypost/core/collection_variable_import.py#L62-L224) inside `accept()`. Refactoring into a Model-View-Presenter (MVP) architecture would allow headless unit testing of dialog presentation logic without instantiating Qt widgets.
2. **Repeated Table Traversal for Preview Summary Calculation**:
   - Every user action (toggling a row checkbox, switching a strategy dropdown, or clicking bulk actions) invokes [`_update_preview_summary`](file:///home/src/pypost/ui/dialogs/import_collection_variables_dialog.py#L471-L506), which performs an $O(N)$ loop over all table rows, resolving each row's selection state and combo box value. While instantaneous for collections with dozens of variables, an incremental counter or reactive model would eliminate unnecessary table scans.
3. **Hardcoded Column Indices**:
   - Column positions (`COL_SELECT = 0` through `COL_DESC = 8`) are defined as module-level integer constants. While legible, changes to column order or adding future metadata columns require updating index references across multiple methods throughout the dialog.

## Missing Tests

1. **Large Dataset Performance Benchmarks**:
   - The test suite verifies functionality, secret masking, per-row resolution, and bulk toggling with representative collections (up to 10 variables). However, automated performance benchmark tests measuring table instantiation time, memory footprint, and summary recount latency for 500 to 1,000+ variables are not yet implemented.
2. **Complex Multi-Step Preset Switching with Partial Customizations**:
   - While tests cover preset value changes and individual row strategy modifications separately, an automated test simulating a compound interactive session (e.g. select Preset A -> click Bulk Overwrite -> customize two specific keys back to Keep Current -> switch to Preset B -> verify kept choices and masked secrets remain preserved) is currently missing.
3. **Keyboard Navigation and Accessibility**:
   - Unit tests verify programmatic interactions (clicks, method calls), but do not exercise keyboard tab ordering or focus traversal into embedded `QComboBox` cell widgets within `QTableWidget`.
4. **Test Timeout Compliance**:
   - All tests in [`tests/test_workspace_environment_import_diff_repro.py`](file:///home/src/tests/test_workspace_environment_import_diff_repro.py) contain explicit `@pytest.mark.timeout(30)` annotations and module-level `pytestmark = [pytest.mark.timeout(30)]`. There are zero missing timeout markers, fully satisfying the `do-testing` contract.

## Performance Concerns

1. **`QTableWidget` Overhead for Large Variable Sets**:
   - For collections containing hundreds or thousands of variables, allocating 9 `QTableWidgetItem` objects and separate `QComboBox` cell widgets per colliding row incurs noticeable heap and layout overhead. This is a known architectural trade-off that will be resolved by virtualized model-view rendering.
2. **Redundant Summary Recalculations**:
   - Rapidly clicking bulk buttons or toggling checkboxes executes a full row scan each time. An incremental state tracker would reduce this from $O(N)$ to $O(1)$.

## Follow-up Tasks

1. **`NON-BLOCKER — pre-existing`: Pre-existing lockfile drift in `requirements-dev.txt` causes `test_repro_check_lock_dev_detects_no_drift` failure**:
   - Jira: [PYPOST-1397](https://pypost.atlassian.net/browse/PYPOST-1397)
   - Test node: `tests/test_lockfile_verification.py::test_repro_check_lock_dev_detects_no_drift`
   - Description: `requirements-dev.txt` is stale relative to `requirements-dev.in` on the base commit, causing `make check-lock-dev` to fail during full test runs.
2. **`NON-BLOCKER — pre-existing`: Makefile test suites time out on shared base venv lock under full-suite parallel load**:
   - Jira: [PYPOST-1413](https://pypost.atlassian.net/browse/PYPOST-1413)
   - Test nodes:
     - `tests/test_makefile_target_install_test.py::TestTargetInstallTest::*`
     - `tests/test_makefile_target_filtering.py`
     - `tests/test_makefile_stamp_otel_idempotency.py`
     - `tests/test_makefile_stamp_test_idempotency.py`
     - `tests/test_makefile_install_stamp_contract.py`
   - Description: Heavy concurrent test execution leads to contention on virtual environment file locks, triggering worker timeouts.
3. **`Follow-up Enhancement`: Virtualized Table Model and Background Fetching for Remote Collections**:
   - Jira: [PYPOST-1415](https://pypost.atlassian.net/browse/PYPOST-1415)
   - Description: Upcoming sprint task to replace `QTableWidget` with a virtualized `QTableView` and `QAbstractTableModel`, implement a `QStyledItemDelegate` for conflict strategy dropdowns, and offload remote collection reading in `library_service` to a background worker to ensure smooth 60 FPS UI performance for 1,000+ variables.
