# PYPOST-64: Observability

No logging changes. Existing events unchanged:

| Location | Level | Event |
|----------|-------|-------|
| `refresh()` | DEBUG | `history_panel_refreshed` |
| `_on_load_into_editor()` | INFO | `history_load_into_editor` |
| `_on_clear_history()` | INFO | `history_cleared` |
| `_copy_as_curl()` | INFO/ERR | `history_curl_copied` / `history_curl_copy_failed` |
