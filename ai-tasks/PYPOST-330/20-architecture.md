# PYPOST-330: Architecture — Delete confirmation branching tests

## Research

- `CollectionTreeActions.show_context_menu` calls `QMessageBox.question` after Delete
  is chosen; `reply != QMessageBox.Yes` records `cancelled` and returns early.
- `handle_delete` records `succeeded` after persistence succeeds.
- PYPOST-329 added `tests/test_collection_tree_actions.py` for menu dispatch and tree
  state without metric assertions.
- `test_collections_presenter.py` has partial Yes/No tests with `FakeMetrics` no-op.

## Implementation Plan

### Phase 1 — New test module

Create `tests/test_collection_tree_delete_confirmation.py`:

| Test | Asserts |
|------|---------|
| `test_collection_delete_no_records_cancelled_metric` | No → cancelled, tree kept |
| `test_collection_delete_yes_records_succeeded_metric` | Yes → succeeded, row removed |
| `test_request_delete_no_records_cancelled_metric` | Request No → cancelled |
| `test_request_delete_yes_records_succeeded_metric` | Request Yes → succeeded |
| `test_delete_no_skips_handle_delete` | No → `handle_delete` not called |

### Phase 2 — Harness

- Reuse presenter + fake `RequestManager` pattern from `test_collection_tree_actions.py`.
- Use `MagicMock` for `MetricsManager` to assert `track_gui_collection_delete_action`
  call order via `assert_has_calls`.
- Patch `QMenu` and `QMessageBox` under `pypost.ui.presenters.collection_tree_actions`.

### Phase 3 — Documentation

- Extend `doc/dev/collection_tree_actions.md` and `collection_item_delete.md` test tables.

## Non-goals

- No production code changes unless a test reveals a defect.
- No coverage of `error` / `not_found` delete metrics (PYPOST-331).
