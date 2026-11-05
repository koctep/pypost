# PYPOST-1427: Observability

## Logging Added / Extended

All messages use the `pypost.ui.models.collection_variables_table_model` logger
at **DEBUG** (high-volume chunk traffic must not flood INFO in production).

| Event | Fields |
| ----- | ------ |
| `collection_variables_table_model_loaded` | `collection_name`, `row_count`, `collisions`, `preset`, `cached_records` (0 after load), `chunk_size`, `max_cached_chunks` |
| `collection_variables_table_model_chunk_fetched` | `chunk_idx`, `start_row`, `end_row`, `rows`, `cached_chunks` |
| `collection_variables_table_model_chunk_evicted` | `chunk_idx`, `rows`, `cached_chunks`, `cached_records` |
| `collection_variables_table_model_preset_updated` | `preset`, `row_count`, `evicted_chunks` |
| `collection_variables_table_model_strategy_changed` | `row`, `var_name`, `strategy` (unchanged) |
| `collection_variables_table_model_bulk_strategy_set` | `strategy`, `affected_rows`, `total_rows`, `cached_records` |

## Metrics

No new Prometheus/OTel instruments in this task. Cache pressure is observable via
DEBUG eviction/fetch pairs and the public `cached_record_count` property for
tests and interactive debugging.

## Validation

- Extreme-catalog repro exercises load → sparse access → eviction paths.
- Enable DEBUG on `pypost.ui.models.collection_variables_table_model` to verify
  `cached_records=0` on load and subsequent `chunk_fetched` / `chunk_evicted`
  sequences while scrolling large catalogs.
