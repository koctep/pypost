# PYPOST-345: Observability

## Metric under test

`gui_collection_rename_actions_total{item_type,status}` via
`MetricsManager.track_gui_collection_rename_action(item_type, status)`.

## Statuses covered by delegate e2e tests

| Status | Test |
| --- | --- |
| `selected` | All four e2e tests (via context menu before edit) |
| `succeeded` | Request and collection commit via delegate |
| `cancelled` | Request cancel via delegate `closeEditor` |
| `rejected_empty` | Request empty commit via delegate |

No new logging or metrics instrumentation; tests assert existing emission through the full
delegate path.
