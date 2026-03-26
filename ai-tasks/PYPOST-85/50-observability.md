# PYPOST-85: Observability

## Assessment

Test-only change to `FakeStorageManager` and `test_request_manager.py`. No production runtime
paths modified.

## Logging / Metrics / Alerting

**N/A.** No executable application code changed.

## Future consideration

If `FakeStorageManager` gains more persistence simulation helpers, keep them on the public
surface so tests stay decoupled from `_collections`.
