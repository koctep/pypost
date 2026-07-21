# PYPOST-829: Dev Docs Update

## Summary

Documented H3-confirmed storage-gateway worker teardown (`deleteLater` + short
`wait(100)`), WARNING event names, troubleshooting, and the permanent stress
canary. Both env and collection gateways are covered.

## Changes

- `doc/dev/environment_storage_async.md` — worker finish teardown section;
  corrected `pypost/core/qt/` module paths; WARNING
  `environment_storage_gateway_worker_finish_wait_timeout`; troubleshooting for
  wait timeout and historical segfault; H3 canary in Tests
- `doc/dev/collection_loading.md` — same teardown for
  `CollectionStorageGateway`; observability; troubleshooting rows; Tests; link to
  async env storage
- `doc/dev/logging.md` — `collection_storage_gateway_*` levels include WARNING
- `doc/dev/gui_testing.md` — H3 stress canary note; segfault troubleshooting row

No user-facing docs (lifecycle hygiene only).

## Key developer guidance

1. On `QThread.finished`, capture worker → clear `_worker` → `deleteLater()` →
   short `wait(_WORKER_FINISH_WAIT_MS)` → drain pending on a **new** worker.
2. Bound stays small (100 ms); never unbounded GUI `wait()`.
3. WARNING only on wait timeout; happy-path finish is silent.
4. Regression: `tests/test_storage_gateway_h3_stress.py`.

## Validation

- [x] Env and collection async docs describe finish teardown
- [x] WARNING event names documented
- [x] Stress canary and troubleshooting linked
- [x] Logging catalog updated for collection gateway WARNING
- [x] Artifact `70-dev-docs.md` created
- [x] Roadmap STEP 7 marked complete
