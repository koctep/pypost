# PYPOST-330: Observability

## Scope

Tests only. No new logs or metrics introduced.

## Instrumentation under test

`CollectionTreeActions.show_context_menu` delete path:

| User action | Metric status | Log (INFO) |
|-------------|---------------|------------|
| Delete chosen | `selected` | `collection_item_delete_selected` |
| Confirm No | `cancelled` | `collection_item_delete_cancelled` |
| Confirm Yes → success | `succeeded` | `collection_item_delete_succeeded` |

Counter: `gui_collection_delete_actions_total{item_type,status}` via
`MetricsManager.track_gui_collection_delete_action`.

## Out of scope

`error` and `not_found` statuses on `handle_delete` — covered by PYPOST-331.
