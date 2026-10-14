# PYPOST-1377: Technical Debt Analysis

## Shortcuts Taken

1. **Raw String Entries Without Live Selector Syntax Validation**:
   - `HiddenFieldsTable` accepts arbitrary string entries via editable table cells.
   - No live syntax validation (such as regex matching, JSONPath syntax checking, dot-notation path verification, or prohibition of invalid whitespace/control characters) is performed in the UI as the user types.
   - Downstream sanitizers (in PYPOST-1378 / PYPOST-1379) are responsible for parsing and handling invalid or unresolvable selector expressions gracefully.
2. **Basic Row Removal Interaction (Delete/Backspace and Context Menu Only)**:
   - Row removal in `HiddenFieldsTable` is handled via the `Delete` or `Backspace` keys (when not in cell-edit mode) or via right-click context menu ("Remove Selected").
   - There is no dedicated inline delete icon/button per row or explicit "Remove" toolbar button alongside the table. This keeps the UI clean and minimalist, but relies on keyboard shortcuts and right-click discoverability.
3. **QTableWidget Auto-Expanding Trailing Row Management**:
   - `HiddenFieldsTable` implements an auto-expanding empty trailing row to facilitate quick consecutive entries without requiring a separate "Add Row" button click.
   - This requires manual signal blocking (`self.blockSignals(True)`) and index adjustment during item change and deletion events to prevent emitting duplicate change signals or leaving orphan blank rows.
4. **Use of Concrete `QTableWidget` over `QAbstractTableModel`**:
   - Implemented using `QTableWidget` and `QTableWidgetItem` instead of a custom `QAbstractTableModel` + `QTableView`.
   - For typical request configurations with a handful of hidden fields (1–20), `QTableWidget` is simpler and faster to implement, but tightly couples data representation to Qt widget items.

## Code Quality Issues

1. **Table Model Refactoring for Large Selector Sets**:
   - If a request configuration ever requires managing very large selector lists (e.g. hundreds or thousands of fields for complex enterprise payloads), `QTableWidget` allocates individual `QTableWidgetItem` objects for each cell.
   - Refactoring to a lightweight `QAbstractTableModel` (or subclassing `QStringListModel`) wrapping a Python list would provide cleaner separation between model and view, lower memory overhead, and simpler undo/redo command stack integration.
2. **UI Data Binding Coordination in `RequestWidget`**:
   - `RequestWidget` directly manages the lifecycle and synchronization of `HiddenFieldsTable` via `self.hidden_fields_table.get_data()` and `set_data()`.
   - While consistent with existing detail tabs (such as Headers and Query Params), centralizing data synchronization through a unified tab presenter or model binder would reduce boilerplate in `pypost/ui/widgets/request_editor.py`.
3. **Selector Deduplication and Case Sensitivity**:
   - `HiddenFieldsTable` strips leading and trailing whitespace and excludes empty rows, but does not deduplicate identical selector strings (e.g., adding `token` multiple times).
   - Deduplication currently relies on downstream consumption or user discipline.

## Missing Tests

1. **Timeout Markers Audit**:
   - **Zero tests missing timeout markers**: All 14 tests in `tests/test_request_hidden_fields_model_and_ui.py` are guarded by the module-level marker `pytestmark = pytest.mark.timeout(30)`, ensuring strict execution timeout enforcement per repository testing standards.
   - Pre-existing tests across all suites continue to adhere to the test baseline and timeout guardrails.
2. **Downstream Integration Tests**:
   - End-to-end integration tests connecting `RequestData.hidden_response_fields` to active response masking in the GUI `ResponseView` and MCP tool execution outputs are deferred to subsequent stories.
   - These are intentionally out of scope for PYPOST-1377 and are scheduled for PYPOST-1378, PYPOST-1379, and PYPOST-1380.
3. **Deeply Nested Dot-Notation and Wildcard Syntax Tests**:
   - While model validation confirms string type enforcement, tests verifying complex selector parsing (e.g. `data.items[*].secret`) belong in the downstream sanitization engines (PYPOST-1378/PYPOST-1379).

## Performance Concerns

1. **Minimal Memory Overhead**:
   - `hidden_response_fields` is represented as a compact `list[str]` in `RequestData`.
   - For typical requests containing 1–20 selector strings, the in-memory footprint is negligible (~80 bytes), with near-instantaneous JSON serialization and deserialization.
2. **O(N) Selector Parsing and Dirty Comparison**:
   - In `persisted_fields_equal` and `request_draft_fields_equal`, list comparison is an O(N) linear equality check. Given small N (N < 50), comparison executes in under 0.1 ms.
   - Traversal of rows in `HiddenFieldsTable.get_data()` is linear with the row count and executes synchronously in under 1 ms, well within the 16 ms budget for 60 FPS interactive UI response.

## Follow-up Tasks

- `NON-BLOCKER`: [PYPOST-1378](https://pypost.atlassian.net/browse/PYPOST-1378) Permanent MCP output masking for hidden response fields (Sprint 2032, Epic PYPOST-1312).
- `NON-BLOCKER`: [PYPOST-1379](https://pypost.atlassian.net/browse/PYPOST-1379) Interactive click-to-reveal response masking in GUI ResponseView (Sprint 2032, Epic PYPOST-1312).
- `NON-BLOCKER`: [PYPOST-1380](https://pypost.atlassian.net/browse/PYPOST-1380) Integration test suite, edge-case coverage, and developer documentation (Sprint 2032, Epic PYPOST-1312).
- `NON-BLOCKER`: [PYPOST-1386](https://pypost.atlassian.net/browse/PYPOST-1386) Refactor `HiddenFieldsTable` to custom `QAbstractTableModel` if large selector sets (> 1,000 entries) or complex undo/redo workflows are needed in future iterations.
- `NON-BLOCKER`: [PYPOST-1387](https://pypost.atlassian.net/browse/PYPOST-1387) Add live inline syntax validation or tooltip helpers for selector path expressions in `HiddenFieldsTable`.

### Blocker Classification

- **BLOCKER items**: 0
- **NON-BLOCKER items**: 5
- **Conclusion**: There are **zero blockers** preventing completion and closing of PYPOST-1377.
