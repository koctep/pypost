# PYPOST-344: Observability

No new logs or metrics. Rename/delete telemetry remains in `CollectionTreeActions`:

- `collection_item_rename_*` / `collection_item_delete_*` log events
- `gui_collection_rename_actions_total` / `gui_collection_delete_actions_total` metrics

Dialog helpers are presentation-only and do not emit telemetry.
