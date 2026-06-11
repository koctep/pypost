# PYPOST-94: Architecture — verify indexed restore (PYPOST-390)

## Research

Original concern (`ai-tasks/PYPOST-10/40-tech-debt.md`): `restore_tree_state` walked every
root row and checked membership in the saved expanded list — O(N) per restore.

PYPOST-390 introduced `_collection_items_by_id` and changed restore to iterate only saved
expanded ids with dict lookup.

## Current Design (verified)

| Component | Role |
|-----------|------|
| `_collection_items_by_id` | `dict[str, QStandardItem]` maintained on rebuild/insert/remove |
| `restore_tree_state` | `for collection_id in get_expanded_collections()` → O(1) lookup → expand |
| `_find_collection_item` | Uses same index for collection rows (no duplicate root scan) |

## Complexity

| Operation | Before | After (PYPOST-390) |
|-----------|--------|---------------------|
| Restore | O(N) root rows | O(E) expanded ids, E ≪ N typical |

## Behavior Preservation

- PYPOST-389: stale ids skipped (lookup miss).
- PYPOST-391: subset expansion — only listed ids expanded.
- Request row lookup in `_find_collection_item` still scans children (unchanged, out of scope).

## Tests (existing — no new code required)

| Test | Scenario |
|------|----------|
| `test_restore_tree_state_expands_via_collection_index` | 50 collections; 2 expanded |
| `test_collection_index_updated_on_incremental_insert_and_remove` | Index sync |
| `test_restore_tree_state_skips_stale_saved_collection_ids` | Stale ids |
| `test_restore_tree_state_expands_only_collections_in_saved_list` | Subset |
| `test_restore_tree_state_expands_known_ids` | Basic restore |

## Step 3 Outcome

No implementation changes — verification confirms PYPOST-390 satisfies PYPOST-94 acceptance
criteria.
