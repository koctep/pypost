# PYPOST-340: Architecture — Index-assisted delete evaluation

## Evaluation Summary

| Operation | Before PYPOST-340 | After PYPOST-340 |
| --- | --- | --- |
| Lookup by ID | O(1) via `_request_index` (PYPOST-333) | unchanged |
| Remove from collection list | O(m) list comprehension | O(m) targeted `del` |
| Index update after delete | O(N) full `_rebuild_index()` | O(1) per request removed |
| `delete_collection` index | O(N) full rebuild | O(k) drop k requests in collection |

N = total requests across all collections; m = requests in target collection; k =
requests in deleted collection.

## Decision

Keep index-assisted lookup from PYPOST-333. Replace full index rebuild on delete with
incremental helpers:

- `_drop_request_from_index(request_id)` — single-key removal
- `_drop_collection_requests_from_index(collection)` — batch removal for collection
  delete

Full `_rebuild_index()` remains for `reload_collections`, `save_request`, and rename
paths where multiple entries may change.

## Implementation Plan

### Phase 1 — Helpers

Add `_drop_request_from_index` and `_drop_collection_requests_from_index` on
`RequestManager`.

### Phase 2 — Wire delete paths

- `delete_request`: locate collection via index, `del` from list, drop one index key.
- `delete_collection`: drop all collection request keys, remove collection from list.

### Phase 3 — Tests

Extend `tests/test_request_manager.py`:

| Test | Asserts |
| --- | --- |
| `test_delete_request_uses_incremental_index_update` | `_rebuild_index` not called |
| `test_delete_collection_uses_incremental_index_update` | `_rebuild_index` not called |
| `test_delete_request_large_collection_keeps_index_consistent` | 500-request stress |

### Phase 4 — Documentation

Document index-assisted delete complexity in `doc/dev/collection_item_delete.md`.

## Non-goals

- Secondary indexes (collection-by-id map) — collection count is small today.
- Async or background index maintenance.
- Changing storage or UI refresh strategy.
