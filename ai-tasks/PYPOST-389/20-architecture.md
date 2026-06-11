# PYPOST-389: Architecture — stale collection id edge case

## Research

`CollectionsPresenter.restore_tree_state()` iterates root-level collection rows and expands
only those whose id appears in `StateManager.get_expanded_collections()`. Unknown ids in the
saved list are naturally skipped because no matching tree item exists.

Relevant production code:

- `pypost/ui/presenters/collections_presenter.py` — `restore_tree_state()`
- `pypost/core/state_manager.py` — `expanded_collections` persistence

Existing test (from PYPOST-93):

| Test | Scenario |
|------|----------|
| `test_restore_tree_state_skips_stale_saved_collection_ids` | Saved list `["deleted-collection", "c1"]`; only `c1` expands |

## Implementation Plan

1. Confirm the presenter test exercises stale-id skip and valid-id restore.
2. Align test docstring with PYPOST-389 task id.
3. Document the test in `doc/dev/collection_tree_actions.md` (already listed under
   PYPOST-388 table).
4. Mark PYPOST-8 tech-debt edge-case item resolved.

No production code changes required.

## Q&A

- **Q:** Separate StateManager persistence test for stale ids? **A:** Not needed — presenter
  test covers restore behavior; persistence format is unchanged.
