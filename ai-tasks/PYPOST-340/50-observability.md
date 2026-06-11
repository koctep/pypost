# PYPOST-340: Observability

## Scope

Performance-oriented change. Existing structured logs on delete paths are unchanged:

| Event | Level |
| --- | --- |
| `delete_request_started` | info |
| `delete_request_succeeded` | info |
| `delete_request_not_found` | warning |
| `delete_collection_started` | info |
| `delete_collection_succeeded` | info |
| `delete_collection_not_found` | warning |

## Metrics

No new metrics. Delete telemetry remains `gui_collection_delete_actions_total` in the
UI layer (PYPOST-35 / PYPOST-339).

## Validation

Index consistency is verified by unit tests, not runtime probes.
