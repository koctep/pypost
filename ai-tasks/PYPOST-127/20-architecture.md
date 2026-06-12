# PYPOST-127: Architecture — Request ID index

## Design

`RequestManager` maintains `_request_index: dict[str, tuple[RequestData, Collection]]`
mapping request ID to the live request object and its parent collection.

```text
reload_collections / save_request
        → _rebuild_index()  (O(N) full scan)

find_request(id)
        → _request_index.get(id)  (O(1))

rename_request(id)
        → _request_index.get(id)  (O(1), no rebuild — ID unchanged)

delete_request / delete_collection
        → incremental _drop_*_from_index  (O(1) per removed ID)
```

N = total requests across collections.

## Implementation Plan

### Phase 1 — Index structure

Add `_request_index` in `__init__`; call `_rebuild_index()` from `reload_collections`.

### Phase 2 — Lookup

Implement `find_request` as `_request_index.get(request_id)`.

### Phase 3 — Maintenance

| Operation | Index update |
| --- | --- |
| `reload_collections` | Full rebuild |
| `save_request` | Full rebuild |
| `delete_request` | Drop one key |
| `delete_collection` | Drop all keys in collection |
| `rename_request` | No rebuild (same ID and object refs) |
| `rename_collection` | Full rebuild (collection object identity unchanged) |

### Phase 4 — Tests

Extend `tests/test_request_manager.py`:

| Test | Asserts |
| --- | --- |
| `test_find_request_uses_index_lookup` | `dict.get` on index |
| `test_reload_collections_rebuilds_index_from_storage` | Index after reload |
| `test_rename_request_uses_index_without_rebuild` | No `_rebuild_index` on rename |
| Delete index tests (PYPOST-340) | Incremental drop, large collection |

## Non-goals

- Collection-by-id secondary index (collection count is small).
- Changing `StorageManager` or presenter APIs.
