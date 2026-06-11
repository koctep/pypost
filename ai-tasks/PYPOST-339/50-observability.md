# PYPOST-339: Observability

## Scope

Tests only. No new logs or metrics introduced.

## Instrumentation under test

`CollectionTreeActions.handle_delete` failure paths:

| Outcome | Metric status | Dialog |
|---------|---------------|--------|
| `delete_collection_item` raises | `error` | critical |
| `delete_collection_item` returns False | `not_found` | warning |

Counter: `gui_collection_delete_actions_total{item_type,status}` via
`MetricsManager.track_gui_collection_delete_action`.

Item types exercised: `collection`, `request`.

## Covered elsewhere

| Status | Module |
|--------|--------|
| `selected`, `cancelled`, `succeeded` | `tests/test_collection_tree_delete_confirmation.py` (PYPOST-330) |

## Out of scope

Live Prometheus scrape validation; metrics server startup.
