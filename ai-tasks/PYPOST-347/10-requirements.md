# PYPOST-347: Incremental tree updates on collection rename

## Goals

Renaming a collection or request in the sidebar should feel instant even when the user
maintains a large number of collections and requests. Today, completing or cancelling a rename
rebuilds the entire tree, which is unnecessary work when only one label changed.

## User Stories

- As a developer with many saved requests, I want rename to update only the edited row so the
  sidebar stays responsive.
- As a user cancelling a rename, I want the tree to show the previous name without a visible
  full-tree flicker or loss of expansion state.

## Definition of Done

- Rename commit updates the edited tree item label in place (request and collection).
- Rename cancel restores the canonical label without rebuilding the full model.
- Rename validation failures (empty name, backend error) restore the prior label without a
  full rebuild when the item is still in the model.
- Expansion state is preserved across rename success and cancel (no `restore_tree_state` needed
  when the tree is not rebuilt).
- Automated tests cover incremental success/cancel paths and assert `refresh_tree` is not called.
- Full test suite passes.

## Task Description

Follow-up to PYPOST-36 performance debt: `_on_editor_closed` in `CollectionsPresenter` calls
`refresh_tree()` on success and cancel. PYPOST-334 established incremental delete via
`remove_item_from_tree`; this task applies the same principle to rename.

## Q&A

- **Q:** Should every rename error path avoid full reload? **A:** Yes, when the target item
  remains in the model; fallback to `refresh_tree` only if the item cannot be located.
- **Q:** Does disk data change on rename? **A:** Yes, via `RequestManager`; in-memory
  collections are already updated — the tree only needs to reflect that single change.
