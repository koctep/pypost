# PYPOST-347: Observability

## Existing Logging (unchanged)

Rename lifecycle logs in `_on_editor_closed` remain:

- `collection_item_rename_cancelled`
- `collection_item_rename_rejected_empty`
- `collection_item_rename_failed`
- `collection_item_rename_not_found`
- `collection_item_rename_succeeded`

Metrics via `track_gui_collection_rename_action` unchanged.

## New Logging

- **WARNING** `collection_item_rename_tree_sync_fallback` — emitted when incremental sync cannot
  find the tree item and falls back to `refresh_tree`.

## Metrics

No new metrics. Rename action counters still reflect user outcomes; performance improvement is
implicit (fewer `refresh_tree_completed` log lines on rename).

## Performance Signal

`refresh_tree_completed` should no longer appear on typical rename success/cancel paths; monitor
log volume in large-tree scenarios if needed.
