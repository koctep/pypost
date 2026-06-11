# PYPOST-329: Observability

## Scope

This task adds automated tests only. No new logs or metrics were introduced.

## Existing instrumentation (unchanged)

`CollectionTreeActions` already logs and records metrics on menu actions:

- `collection_request_open_new_tab` — INFO on New tab
- `collection_item_rename_selected` — INFO on Rename
- `collection_item_delete_selected` / `collection_item_delete_cancelled` — INFO on Delete

Metrics: `track_gui_new_tab_action`, `track_gui_collection_rename_action`,
`track_gui_collection_delete_action` (see `doc/dev/collection_item_delete.md`).

## Follow-up

Metric label assertions remain out of scope — see PYPOST-331.
