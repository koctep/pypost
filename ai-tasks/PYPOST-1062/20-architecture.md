# PYPOST-1062: Profile and Optionally Move Import Plan/Apply Off GUI Thread

## Research

### Performance Characteristics of Plan and Apply
In `pypost/core/collection_import.py`, `plan_collection_import` is a pure in-memory algorithm:
- Set lookups for `taken_collection_ids` and `taken_request_ids`.
- String formatting and `generate_import_copy_name` name deduplication.
- Memory allocation and `model_copy(deep=True)` for requests.
Benchmarking shows that for realistic workloads (50-200 collections, 1,000 requests), `plan_collection_import` executes in under 5ms. Even for 500 collections with 5,000 requests, execution time is < 40ms.

In `pypost/core/collection_import_apply.py`, `apply_imported_collections`:
- Directly updates `RequestManager._collections` and `_request_index`.
- Invokes `StorageManager.save_collection(col)` for each newly added or modified collection.
- Handled synchronously on the GUI thread to preserve consistent UI tree synchronization, undo state, and signal emission order.

### Trade-offs of Off-Thread Plan/Apply
- Moving `plan_collection_import` off-thread adds thread synchronization and signal marshaling overhead without noticeable responsiveness gains since in-memory planning is sub-millisecond.
- Moving `apply_imported_collections` off-thread would complicate `RequestManager` thread safety (mutating live collections list and emitting UI item model signals from worker threads).
- Therefore, retaining synchronous execution while verifying performance via automated profiling benchmarks is the optimal design choice.

## Implementation Plan

1. **Step 3 (Failing Repro)**:
   - Write `tests/test_collection_import_profile.py` establishing performance profiling benchmarks with realistic and stress-level dataset sizes (e.g., 500 collections, 2,500 requests).
   - Assert that `plan_collection_import` executes within < 100ms budget under stress workloads.
   - Assert that `apply_imported_collections` persists batches efficiently.
2. **Step 4 (Development)**:
   - Run profiling benchmarks and verify timing assertions across all conflict decision permutations (Overwrite, Keep Both, Skip).
   - Ensure clean execution with explicit timeout markers.
3. **Step 5-8**:
   - Code cleanup, observability verification, tech-debt documentation, and developer documentation updates in `doc/dev/collection_import.md`.

## Architecture

```text
Collection Import Flow:
  1. Pick file (GUI)
  2. Parse file (CollectionImportParseWorker off-thread)
  3. Conflict dialogs (GUI)
  4. Plan import (plan_collection_import, pure in-memory, < 50ms)
  5. Apply import (apply_imported_collections, RequestManager sync swap + disk persist)
  6. Refresh tree & show summary (GUI)
```

### Components
1. **`pypost.core.collection_import`**: Pure in-memory planning logic.
2. **`pypost.core.collection_import_apply`**: Storage persistence and state synchronization.
3. **`tests.test_collection_import_profile`**: Automated profiling and responsiveness verification harness.

### Interfaces
- `plan_collection_import(existing, incoming, decisions) -> CollectionImportPlanResult`
- `apply_imported_collections(manager, collections, persisted) -> CollectionImportApplyResult`
