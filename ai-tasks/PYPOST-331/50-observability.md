# PYPOST-331: Observability

## Scope

Verification of existing test coverage. No new logs or metrics introduced.

## Full status matrix under test

Counter: `gui_collection_delete_actions_total{item_type,status}` via
`MetricsManager.track_gui_collection_delete_action`.

### Confirmation boundary (`show_context_menu`)

| User action | Status | Test module |
|-------------|--------|-------------|
| Delete chosen | `selected` | `test_collection_tree_delete_confirmation` |
| Confirm No | `cancelled` | `test_collection_tree_delete_confirmation` |
| Confirm Yes → success | `succeeded` | `test_collection_tree_delete_confirmation` |

### `handle_delete` failure paths

| Outcome | Status | Test module |
|---------|--------|-------------|
| `delete_collection_item` raises | `error` | `test_collection_tree_delete_metrics` |
| `delete_collection_item` returns False | `not_found` | `test_collection_tree_delete_metrics` |

Item types exercised: `collection`, `request` in both modules.

## Validation results

- [x] All five status values covered by automated tests
- [x] Failure paths do not emit spurious `succeeded`
- [x] Tests run headlessly with `QT_QPA_PLATFORM=offscreen`

## Out of scope

Live Prometheus scrape validation; metrics server startup.
