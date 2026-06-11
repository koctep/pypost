# PYPOST-391: Architecture — Qt UI state preservation test

## Research

`CollectionsPresenter.restore_tree_state()` walks root-level collection rows and calls
`QTreeView.expand(index)` only for ids in `StateManager.get_expanded_collections()`. With
multiple collections loaded, the widget must reflect subset expansion — not all rows expanded.

Existing test (from PYPOST-95, formalized for PYPOST-8):

| Test | Scenario |
|------|----------|
| `test_restore_tree_state_expands_only_collections_in_saved_list` | Two collections; saved `["c2"]`; only second row expanded |

Related coverage (other tasks):

| Test | Task |
|------|------|
| `test_tree_expansion_saved_and_restored_after_reload` | Round-trip expand → reload → restore |
| `test_restore_tree_state_skips_stale_saved_collection_ids` | PYPOST-389 stale ids |

## Implementation Plan

1. Confirm presenter test uses real `QTreeView` and `isExpanded` assertions.
2. Align test docstring with PYPOST-391 task id.
3. Document test in `doc/dev/collection_tree_actions.md` (PYPOST-388 table).
4. Mark PYPOST-8 tech-debt UI preservation item resolved.

No production code changes required.

## Q&A

- **Q:** Mock `QTreeView`? **A:** No — `CollectionsPresenter` tests use the real widget for
  expansion signals and `isExpanded` checks.
