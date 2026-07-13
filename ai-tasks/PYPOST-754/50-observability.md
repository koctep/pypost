# PYPOST-754: Observability Implementation

## Logging

| Location | Level | Event |
|----------|-------|-------|
| `collection_storage_worker.py` | DEBUG | `collection_storage_worker_run_started` |
| `collection_storage_worker.py` | DEBUG | `collection_storage_worker_load_completed` |
| `collection_storage_worker.py` | ERROR | `collection_storage_worker_load_failed` |
| `collection_storage_gateway.py` | DEBUG | `collection_storage_gateway_load_started` |
| `collection_storage_gateway.py` | DEBUG | `collection_storage_gateway_load_queued` |
| `collection_storage_gateway.py` | INFO | `collection_storage_gateway_pending_load_started` |
| `request_manager.py` | INFO | `apply_loaded_collections_completed` |
| `collections_presenter.py` | INFO | `collection_storage_async_load_dispatched` |
| `collections_presenter.py` | ERROR | `collection_storage_async_load_failed` |
| `collections_presenter.py` | WARNING | `load_collections_async_fallback` |

## Metrics

No new counters in this task. Startup timing spans deferred to a follow-up.

## Verification

- Error-path worker test asserts `load_failed` signal.
- Gateway tests use `QSignalSpy` on `load_completed`.
