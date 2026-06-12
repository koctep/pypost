# PYPOST-127: Technical Debt Analysis

## Shortcuts Taken

- `save_request` still calls full `_rebuild_index()` — acceptable; save frequency is
  low and rebuild is O(N) once per save.
- `rename_collection` still rebuilds index — collection rename does not change request
  IDs; incremental update possible but out of scope.

## Code Quality Issues

- None introduced.

## Missing Tests

- None for this task scope.

## Performance Concerns

- Resolved: `find_request` and `rename_request` lookup are O(1).
- Delete paths use incremental index drop (PYPOST-340).
- Remaining O(m) work: removing a request from its parent list (m = requests in one
  collection).

## Follow-up Tasks

- None — core index requirement satisfied. UI incremental refresh after delete remains
  tracked separately (PYPOST-334).
