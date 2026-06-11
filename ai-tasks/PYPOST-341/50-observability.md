# PYPOST-341: Observability

## Summary

No new logs or metrics. Rename telemetry remains in `CollectionTreeActions`:

- **INFO**: `collection_item_rename_selected`, `collection_item_rename_cancelled`,
  `collection_item_rename_succeeded`
- **WARNING**: `collection_item_rename_rejected_empty`, `collection_item_rename_not_found`,
  `collection_item_rename_not_found_in_model`, `collection_item_rename_tree_sync_fallback`
- **ERR**: `collection_item_rename_failed`
- **Metrics**: `track_gui_collection_rename_action(item_type, status)`

Delegate rejection of empty names triggers `handle_rename_rejected_empty`, preserving
existing log and metric behavior.
