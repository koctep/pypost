# PYPOST-1494: Technical Debt Analysis

## Scope Analysed

Working-tree changes for PYPOST-1494:
- `tests/test_library_import_cancel_checkpoints_repro.py` (Qt-free unit test suite verifying cancellation checkpoints across `list_entries`, `resolve_entries`, and `_resolve_library_candidates`).
- Prior step artifacts (`10-requirements.md`, `20-architecture.md`, `40-code-cleanup.md`, `50-observability.md`).

This task directly resolves **TD-1** from [PYPOST-1324](file:///home/src/ai-tasks/PYPOST-1324/60-tech-debt.md) ("Add Qt-free unit tests for library import cancel checkpoints").

### Timeout Markers (do-testing BLOCKER check)

No blocker. All tests in `tests/test_library_import_cancel_checkpoints_repro.py` declare explicit timeouts:
- Module-level: `pytestmark = pytest.mark.timeout(30)`
- Per-test annotations: `@pytest.mark.timeout(30)` on all 7 test cases
- Internal execution: All tests use in-memory stubs and deterministic cancellation checks without sleeps, threads, or external network/disk resources. Execution time is ~1.18 seconds for the entire suite.

---

## Shortcuts Taken

1. **In-Memory Fake Library Manager Double (`_FakeLibraryManager`)**:
   - Rather than mocking methods on `LibraryManager` via `unittest.mock.patch` or initializing real library management infrastructure, a minimal double implementing `list_connections()` and `get_connection()` was defined directly in the test file.
   - This keeps the tests completely independent of Qt, threading, and persistence logic, but means the double is scoped locally to this module.

2. **Synchronous File System Fixtures via `tmp_path`**:
   - Manifests and collection JSON files are created synchronously in `pytest`'s temporary directory fixture (`tmp_path`). Real file reading is exercised through `find_and_read_manifest` and `load_collection_import_candidates` without network calls.

3. **No Production Code Alterations**:
   - Because production checkpoints implemented in PYPOST-1324 already correctly check tokens and raise `OperationCancelledError`, no production code modifications were necessary. The repro suite serves as regression verification and living specification.

---

## Code Quality Issues

1. **Local Test Double Duplication**:
   - `_FakeLibraryManager` is declared inside `tests/test_library_import_cancel_checkpoints_repro.py`. If future tests need a lightweight library manager double, consider refactoring it to a shared fixture or test helper module (e.g. `tests/fixtures/fake_library_manager.py`).

2. **Residual Code Quality Issues from PYPOST-1324 (Pre-tracked)**:
   - **TD-3 (Low)**: Loose typing in `CollectionImportActions._resolve_library_candidates` and `_resolve_operation` (`cancellation_token: Any | None` instead of `CancellationToken | None`). Tracked in [PYPOST-1495](https://pypost.atlassian.net/browse/PYPOST-1495).
   - **TD-4 (Low)**: `AttributeError` guard retained during `operation_cancelled.disconnect` for spy doubles. Tracked in [PYPOST-1496](https://pypost.atlassian.net/browse/PYPOST-1496).
   - **TD-5 (Low)**: LibraryPresenter lacks cancel/teardown interrupt path. Tracked in [PYPOST-1497](https://pypost.atlassian.net/browse/PYPOST-1497).

---

## Missing Tests

1. **None within the ticket scope**:
   - Coverage is comprehensive for all identified cancellation checkpoints:
     - `list_entries` outer connection loop (pre-cancelled and mid-loop).
     - `list_entries` inner manifest collections loop (mid-loop between collection paths).
     - `resolve_entries` selected entries loop (pre-cancelled and mid-loop).
     - `_resolve_library_candidates` pre-resolution check (pre-cancelled).
     - `_resolve_library_candidates` candidate materialization loop (mid-loop).
     - Baseline execution verifying that uncancelled operations complete successfully without error.

2. **Coarse Cooperative Boundaries (Accepted NFR / TD-7 in PYPOST-1324)**:
   - Cancellation is intentionally verified at discrete loop boundaries between connections, manifest collection paths, and candidate models. Cancellation inside a single `find_and_read_manifest` or `load_collection_import_candidates` I/O read is out of scope and not supported by design.

---

## Performance Concerns

1. **Fast Headless Execution**:
   - The entire unit test file executes 7 tests in ~1.18 seconds, well within the repository fast test suite target (<5s) and comfortably below the 30-second timeout limit.
   - Zero memory leaks, zero hanging threads, and no background event loop accumulation.

---

## Follow-up Tasks

### Pre-existing Issues (NON-BLOCKER — pre-existing)

1. **Line length violation in MCP server registry**:
   - `tests/test_mcp_server_registry.py:308:101: E501 line too long (101 > 100 characters)`
   - Status: `NON-BLOCKER — pre-existing`
   - Jira: [PYPOST-1509](https://pypost.atlassian.net/browse/PYPOST-1509)

2. **Lockfile drift check**:
   - Dev lockfile drift detection tracked in [PYPOST-1397](https://pypost.atlassian.net/browse/PYPOST-1397)
   - Status: `NON-BLOCKER — pre-existing`

3. **Parallel test worker timeout in CI**:
   - Test suites parallel environment timeouts tracked in [PYPOST-1413](https://pypost.atlassian.net/browse/PYPOST-1413)
   - Status: `NON-BLOCKER — pre-existing`

### Connected Follow-up Tasks from PYPOST-1324

1. **[PYPOST-1495](https://pypost.atlassian.net/browse/PYPOST-1495)**:
   - Type annotation tightening: Use `CancellationToken` instead of `Any | None` in `CollectionImportActions`.
   - Priority: Low
   - Status: Open

2. **[PYPOST-1496](https://pypost.atlassian.net/browse/PYPOST-1496)**:
   - Clean up `AttributeError` exception handler in `operation_cancelled.disconnect`.
   - Priority: Low
   - Status: Open

3. **[PYPOST-1497](https://pypost.atlassian.net/browse/PYPOST-1497)**:
   - Add cooperative cancellation and teardown interrupt support to `LibraryPresenter`.
   - Priority: Low
   - Status: Open
