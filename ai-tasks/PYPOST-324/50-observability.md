# PYPOST-324: Observability

No new logs or metrics. Delete telemetry remains in `CollectionTreeActions`:

- `collection_item_delete_*` log lines in `handle_delete` / `show_context_menu`
- `gui_collection_delete_actions_total` via `MetricsManager.track_gui_collection_delete_action`

See `doc/dev/collection_item_delete.md` and `doc/dev/collection_tree_actions.md`.
