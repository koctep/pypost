# PYPOST-326: Observability

No new logs or metrics. Delete-flow telemetry remains in `CollectionTreeActions`:

- `collection_item_delete_selected` / `cancelled` / `succeeded` / `not_found` / `error`
- `gui_collection_delete_actions_total{item_type,status}` via `MetricsManager`

`MainWindow` logs only composition events (`main_window_initialized`, settings, exit).
