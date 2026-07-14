# PYPOST-762: Observability

## New log events

| Logger | Level | Event | Fields |
| --- | --- | --- | --- |
| `pypost.core.history_manager` | INFO | `history_load_async_dispatched` | `path` |
| `pypost.core.history_manager` | INFO | `history_load_async_completed` | `count` |

## Existing events (unchanged)

- `history_manager_loaded` (DEBUG) — still emitted from `_load()`
- `history_manager_load_failed` (WARNING) — corrupt/missing file handling unchanged
- `history_panel_refreshed` (DEBUG) — fires after async load completes via `refresh()`

## Metrics

No new Prometheus counters — P3 startup optimization; duration is available via log
`elapsed_ms` on save path only.
