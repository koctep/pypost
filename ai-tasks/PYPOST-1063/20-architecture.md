# PYPOST-1063: Close Small Async Collection-Import Test Gaps

## Research

### Existing Test Coverage and Gap Analysis
In `tests/test_collections_import_ui.py` and `tests/test_collection_import_responsiveness.py`, the core happy paths, conflict dialog interactions, save error reconciliations, and synthetic delay responsiveness are tested. However, the following gap scenarios identified in `ai-tasks/PYPOST-1005/60-tech-debt.md` remained untested:
1. **Busy re-entry guard**: `CollectionImportActions.import_collections` checks `if self.is_busy(): logger.info("collection_import_skipped reason=busy"); return`. This prevents re-entrant parse worker execution during active file parsing.
2. **Unexpected exceptions during parsing**: `CollectionImportParseWorker.run()` wraps `self._read_import_file(self._path)` in a generic `except Exception as exc: self.parse_failed.emit(exc)`. This path needs regression verification ensuring unhandled reader exceptions are logged and converted to user dialogs without process crashes.
3. **Status message lifecycle assertions**: Verifying that status bar hooks receive `MSG_IMPORT_PREPARING` and `MSG_IMPORT_VALIDATING` sequentially.
4. **Real multi-record JSON file parsing**: Validating end-to-end asynchronous parsing of a genuine file from disk without reader stubbing.

## Implementation Plan

1. **Step 3 (Failing Repro)**:
   - Create `tests/test_collection_import_async_gaps.py` containing:
     - `test_import_skipped_when_already_busy`: Assert second import call while busy is rejected and logs `collection_import_skipped reason=busy`.
     - `test_unexpected_reader_exception_surfaces_invalid_dialog`: Assert unhandled reader exception triggers `collection_import_parse_worker_failed` and displays invalid file error box.
     - `test_status_bar_lifecycle_transitions`: Assert status bar callback sequence.
     - `test_real_json_file_async_import_responsiveness`: Assert end-to-end real file loading.
   - Run tests and confirm test harness correctness.
2. **Step 4 (Development)**:
   - Verify green test suite, ensuring clean caplog contracts and explicit timeout annotations.
3. **Step 5-8**:
   - Code cleanup, observability review, tech-debt recording, and dev doc updates.

## Architecture

```text
CollectionImportActions
  ├── import_collections() ──[is_busy() == True]──> Log INFO skipped & return early
  └── _start_parse()
        └── CollectionImportParseWorker
              ├── Happy Path ──> emit parse_progress / parse_completed
              └── Unexpected Exception ──> catch, log ERROR & emit parse_failed
```

### Components
- `pypost.ui.presenters.collection_import_actions.CollectionImportActions`
- `pypost.core.qt.collection_import_parse_worker.CollectionImportParseWorker`
- `tests.test_collection_import_async_gaps`

## Q&A

### Q1: Why are these tests separated into a dedicated test module?
**A:** `tests/test_collection_import_async_gaps.py` targets asynchronous edge cases, busy-state re-entrancy, and unexpected worker exceptions, keeping them isolated from pure UI unit tests and high-level integration suites.

### Q2: Do these tests require modifications to production code?
**A:** No, the production mechanisms (`is_busy()` guard, exception handling in `CollectionImportParseWorker`, status callback invocations) were implemented in PYPOST-1005 / PYPOST-1061. This task provides formal test verification for previously uncovered edge cases.
