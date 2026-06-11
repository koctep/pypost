# PYPOST-364: Observability

## Existing instrumentation

No new metrics or log lines required. Search actions continue to use:

- `logger.debug("response_search_find ...")` and `response_search_typed ...`
- `MetricsManager.track_gui_response_search_action(source, has_matches)`

## Behaviour note

`has_matches` remains based on `total > 0` from `_update_match_count()`. Capped counting does not
change whether matches exist — only how the total is displayed.

## Future (out of scope)

- Optional debug log when `capped=True` for large-document searches (not added — low diagnostic
  value).
