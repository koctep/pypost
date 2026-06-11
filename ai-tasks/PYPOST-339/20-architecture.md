# PYPOST-339: Architecture — Delete metric status tests

## Research

- `CollectionTreeActions.handle_delete` emits:
  - `error` when `delete_collection_item` raises
  - `not_found` when it returns `False`
  - `succeeded` when delete persists (PYPOST-330)
- `show_context_menu` emits `selected` / `cancelled` before `handle_delete` (PYPOST-330).
- `test_collection_tree_delete_confirmation.py` covers dialog-boundary metrics only.

## Implementation Plan

### Phase 1 — New test module

Create `tests/test_collection_tree_delete_metrics.py`:

| Test | Asserts |
|------|---------|
| `test_collection_delete_error_records_error_metric` | collection + exception → `error` |
| `test_request_delete_error_records_error_metric` | request + exception → `error` |
| `test_collection_delete_not_found_records_not_found_metric` | collection + False → `not_found` |
| `test_request_delete_not_found_records_not_found_metric` | request + False → `not_found` |
| `test_delete_error_does_not_emit_succeeded_metric` | failure does not record `succeeded` |

### Phase 2 — Harness

- Reuse presenter + fake `RequestManager` from confirmation tests; add `delete_result`
  and `delete_error` knobs.
- `MagicMock` metrics; patch `QMessageBox.critical` / `warning` to avoid dialogs.
- Call `handle_delete` directly (metrics under test are post-confirmation).

### Phase 3 — Documentation

- Extend `doc/dev/collection_item_delete.md` testing table with metric status matrix.

## Non-goals

- No production changes unless tests expose a defect.
- No duplication of PYPOST-330 confirmation tests.
