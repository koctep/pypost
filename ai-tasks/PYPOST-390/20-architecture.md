# PYPOST-390: Architecture — collection index for restore

## Research

`CollectionsPresenter.restore_tree_state()` previously walked every root row:

```text
for each root row → if collection id in expanded list → expand
```

Complexity: O(N) collections per restore, even when |expanded| ≪ N.

`CollectionsPresenter` already maintains the tree via `refresh_tree`, incremental
`_insert_collection_into_tree`, and `remove_item_from_tree`. A collection id → `QStandardItem`
map can be kept in sync on those paths.

## Design

| Component | Change |
|-----------|--------|
| `_collection_items_by_id` | `dict[str, QStandardItem]` on presenter |
| `refresh_tree` | Clear and repopulate index when rebuilding model |
| `_insert_collection_into_tree` | Register new collection id |
| `remove_item_from_tree` | Unregister collection id on delete |
| `restore_tree_state` | Iterate `get_expanded_collections()`; O(1) lookup per id |
| `_find_collection_item` | Use index for `item_type == "collection"` |

## Behavior Preservation

- Stale expanded ids: lookup misses → no expand (PYPOST-389).
- Subset expansion: only listed ids expanded (PYPOST-391).
- Request lookup: unchanged linear scan under each collection.

## Tests

| Test | Scenario |
|------|----------|
| `test_restore_tree_state_expands_via_collection_index` | 50 collections; 2 expanded |
| `test_collection_index_updated_on_incremental_insert_and_remove` | Index sync on insert/remove |
| Existing PYPOST-388/389/391 tests | No regression |
