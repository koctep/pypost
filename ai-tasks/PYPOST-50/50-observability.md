# PYPOST-50: Observability

## Summary

No production logging or metrics changes. `StorageManager` retains existing structured logs
and counters; only consumer type hints changed.

## Verification

- Existing `storage_*` log events unchanged in `pypost/core/storage.py`.
- Environment adapter metrics paths unchanged (PYPOST-482).
- Async gateway/worker debug logs unchanged.

## Future

If a non-filesystem backend is added, emit backend-specific metrics from that implementation
while keeping the `StorageInterface` contract stable.
