# PYPOST-127: Dev Docs

## Updates

- **`doc/dev/collection_loading.md`**: Documented `_request_index` structure, O(1)
  lookup on `find_request` / `rename_request`, rebuild vs incremental maintenance, and
  link to PYPOST-127.

## Existing coverage (unchanged)

- `doc/dev/architecture.md` — RequestManager index mention.
- `doc/dev/collection_item_delete.md` — index-assisted delete.
- `doc/dev/testing.md` — RequestManager test matrix.

## Verification

Docs align with `pypost/core/request_manager.py` implementation.
