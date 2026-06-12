# PYPOST-264: Observability

## Metric

`gui_new_tab_actions_total{source=<label>}` — counter for GUI new-tab actions.

## Source Labels

| Label | Trigger |
| --- | --- |
| `plus_button` | Click on trailing `+` tab |
| `shortcut` | Ctrl+N keyboard shortcut |
| `collections_context` | Collection tree context-menu new tab |
| `unknown` | Default parameter or unrecognized caller string |

## Validation Layer

`MetricsRegistry.track_gui_new_tab_action` calls `_normalize_new_tab_source` before
incrementing. Invalid strings map to `unknown`, preventing unbounded label cardinality.

## Logging

Unchanged: `TabsPresenter.handle_new_tab` logs `new_tab_action_triggered source=<source>` at INFO
with the raw caller string (pre-normalization). Metrics use the normalized label.

## Tests

`tests/test_metrics_manager.py`:

- `test_track_gui_new_tab_action_known_sources` — `plus_button`, `shortcut`
- `test_track_gui_new_tab_action_collections_context` — `collections_context`
- `test_track_gui_new_tab_action_invalid_source_maps_to_unknown` — invalid → `unknown`
