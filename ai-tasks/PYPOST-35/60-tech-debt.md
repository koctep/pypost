# PYPOST-35: Technical Debt Analysis

## Shortcuts Taken

- UI context-menu deletion was implemented directly in `MainWindow` methods.
  A separate UI action/controller layer was planned in architecture but not extracted yet.
- Deletion telemetry was added without dedicated metric-focused automated tests.

## Code Quality Issues

- `MainWindow` continues to grow and now includes additional delete-flow responsibilities
  (`show_collection_item_context_menu`, confirmation, result handling, telemetry).
- `StorageManager` still uses `collection.name` as filename; this couples persistence identity
  to mutable display name and can cause collisions if names are duplicated.
- Deleting collection/request does not currently reconcile open tabs that reference deleted items.
  Tabs remain open with stale request data until user action refreshes state.

## Missing Tests

- No automated GUI tests for collection tree right-click context menu behavior.
- No tests for confirmation-dialog branching in delete flow (Yes/No outcomes).
- No tests for emitted metric labels/status values for delete actions.
- No tests for open-tab behavior after deleting a request or its parent collection.

## Performance Concerns

- `RequestManager.delete_request` performs nested search over collections/requests (O(n)).
  This is acceptable for current scale but may degrade with very large collections.
- Tree reload after every delete (`load_collections`) rebuilds full model.
  Incremental model updates could reduce UI work for larger datasets.

## Follow-up Tasks

- Extract collection-tree actions into a dedicated UI controller/helper class to slim `MainWindow`.
- Introduce stable collection file key (ID-based filename) and migration path from name-based files.
- On successful deletion, close or invalidate tabs that point to deleted requests/collections.
- Add GUI/integration tests for context menu + confirmation + model refresh behavior.
- Add tests that assert delete metric emission by status and item type.
- Evaluate index-assisted deletion path in `RequestManager` for large datasets.
