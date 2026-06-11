# PYPOST-354: Observability

## Logging

Unchanged behaviour, consolidated implementation:

- **DEBUG**: `response_search_find source=%s matches=%d` — emitted from `_track_search_result`
  after Next, Previous, and Enter navigation.
- **DEBUG**: `response_search_typed query_len=%d matches=%d` — still in `_on_search_text_changed`.

## Metrics

Unchanged. `gui_response_search_actions_total{source, has_matches}`:

| source | Trigger |
| --- | --- |
| `next` | Next button |
| `previous` | Previous button |
| `enter` | Return in search input |
| `typed` | Debounced/immediate text search |

Navigation sources now route through `_track_search_result`.

## Operational Impact

None. Pure refactor; log and metric cardinality unchanged.
