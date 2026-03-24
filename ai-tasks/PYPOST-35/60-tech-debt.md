# PYPOST-35: Technical Debt Analysis


## Shortcuts Taken

- **Tree delete in MainWindow** ([PYPOST-324](https://pypost.atlassian.net/browse/PYPOST-324)):
  Implemented directly on `MainWindow`; architecture had planned a separate UI controller layer not
  yet extracted.
- Deletion telemetry was added without dedicated metric-focused automated tests.
  — [PYPOST-325](https://pypost.atlassian.net/browse/PYPOST-325)

## Code Quality Issues

- **MainWindow delete-flow growth** ([PYPOST-326](https://pypost.atlassian.net/browse/PYPOST-326)):
  Additional responsibilities (`show_collection_item_context_menu`, confirmation, telemetry) keep
  accumulating in one class.
- **Name-based storage filenames** ([PYPOST-327](https://pypost.atlassian.net/browse/PYPOST-327)):
  `StorageManager` still uses `collection.name` as filename, coupling identity to mutable display
  names and risking collisions.
- **Stale tabs after delete** ([PYPOST-328](https://pypost.atlassian.net/browse/PYPOST-328)):
  Open tabs are not reconciled when items are deleted; they can show stale data until the user
  refreshes.

## Missing Tests

- No automated GUI tests for collection tree right-click context menu behavior.
  — [PYPOST-329](https://pypost.atlassian.net/browse/PYPOST-329)
- No tests for confirmation-dialog branching in delete flow (Yes/No outcomes).
  — [PYPOST-330](https://pypost.atlassian.net/browse/PYPOST-330)
- No tests for emitted metric labels/status values for delete actions.
  — [PYPOST-331](https://pypost.atlassian.net/browse/PYPOST-331)
- No tests for open-tab behavior after deleting a request or its parent collection.
  — [PYPOST-332](https://pypost.atlassian.net/browse/PYPOST-332)

## Performance Concerns

- `RequestManager.delete_request` performs nested search over collections/requests (O(n)).
  — [PYPOST-333](https://pypost.atlassian.net/browse/PYPOST-333)
  This is acceptable for current scale but may degrade with very large collections.
- Tree reload after every delete (`load_collections`) rebuilds full model.
  — [PYPOST-334](https://pypost.atlassian.net/browse/PYPOST-334)
  Incremental model updates could reduce UI work for larger datasets.

## Follow-up Tasks

- Extract collection-tree actions into a dedicated UI controller/helper class to slim `MainWindow`.
  — [PYPOST-335](https://pypost.atlassian.net/browse/PYPOST-335)
- Introduce stable collection file key (ID-based filename) and migration path from name-based files.
  — [PYPOST-336](https://pypost.atlassian.net/browse/PYPOST-336)
- On successful deletion, close or invalidate tabs that point to deleted requests/collections.
  — [PYPOST-337](https://pypost.atlassian.net/browse/PYPOST-337)
- Add GUI/integration tests for context menu + confirmation + model refresh behavior.
  — [PYPOST-338](https://pypost.atlassian.net/browse/PYPOST-338)
- Add tests that assert delete metric emission by status and item type.
  — [PYPOST-339](https://pypost.atlassian.net/browse/PYPOST-339)
- Evaluate index-assisted deletion path in `RequestManager` for large datasets.
  — [PYPOST-340](https://pypost.atlassian.net/browse/PYPOST-340)
