# PYPOST-325: Architecture — Delete metric automated test coverage

## Research

- `MetricsManager.track_gui_collection_delete_action(item_type, status)` records
  `gui_collection_delete_actions_total{item_type,status}`.
- `CollectionTreeActions.show_context_menu` emits `selected` then `cancelled` or
  `succeeded` at the confirmation boundary.
- `CollectionTreeActions.handle_delete` emits `error` or `not_found` on persistence
  failures.
- Existing modules:
  - `tests/test_collection_tree_delete_confirmation.py` (PYPOST-330)
  - `tests/test_collection_tree_delete_metrics.py` (PYPOST-339)

## Implementation Plan

### Phase 1 — Verify coverage matrix

| Status | Item types | Test module |
|--------|------------|-------------|
| `selected` | collection, request | `test_collection_tree_delete_confirmation` |
| `cancelled` | collection, request | `test_collection_tree_delete_confirmation` |
| `succeeded` | collection, request | `test_collection_tree_delete_confirmation` |
| `error` | collection, request | `test_collection_tree_delete_metrics` |
| `not_found` | collection, request | `test_collection_tree_delete_metrics` |

### Phase 2 — Harness pattern

- `CollectionsPresenter` + `MagicMock` metrics + fake `RequestManager`.
- Confirmation tests mock `confirm_delete` and `QMenu`; failure tests call
  `handle_delete` directly and patch dialog helpers.
- `QT_QPA_PLATFORM=offscreen` for headless Qt.

### Phase 3 — Documentation

- Index delete metric tests in `doc/dev/testing.md`.
- Cross-reference `doc/dev/collection_item_delete.md` metric matrix (PYPOST-339).

## Non-goals

- No production code changes unless tests expose a defect.
- No new test module if existing pair covers the full matrix.
