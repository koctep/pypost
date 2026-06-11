# PYPOST-91: Technical Debt Analysis

## Shortcuts Taken

None.

## Code Quality Issues

- **Resolved (PYPOST-91 / PYPOST-387):** Duplicated `isinstance(data, str)` checks in
  `_on_tree_expanded` and `_on_tree_collapsed`. `restore_tree_state` uses `_collection_items_by_id`
  (PYPOST-390) instead of per-row type checks.

## Missing Tests

- Invalid/empty index path for `_is_collection_item` not explicitly tested (returns `False` via
  `item is None`); low risk.

## Performance Concerns

None — helper is O(1) per call; restore is O(expanded) via dict lookup.

## Follow-up Tasks

- **Linear search on restore** — resolved by PYPOST-390 (`_collection_items_by_id`).
- Remaining PYPOST-10 items tracked separately (PYPOST-92, PYPOST-93, PYPOST-94, etc.).

## Verdict

**SAFE TO CLOSE**
