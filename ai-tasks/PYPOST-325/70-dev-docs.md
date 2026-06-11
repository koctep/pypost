# PYPOST-325: Dev Documentation

## Changes Made

### Updated: `doc/dev/testing.md`

- Added **Delete metric unit tests** section indexing confirmation and `handle_delete`
  failure test modules with status matrix and focused run command.

### Existing (PYPOST-330 / PYPOST-339)

- `doc/dev/collection_item_delete.md` — detailed metric matrix and test scenarios.
- `doc/dev/collection_tree_actions.md` — confirmation branching test reference.

## Validation

- [x] Test module names match repository files
- [x] Status labels match `MetricsManager.track_gui_collection_delete_action`
- [x] Focused run command verified (10 tests pass)
