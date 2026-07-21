# PYPOST-829: Observability Implementation

## Scope

H3 confirmed: both storage gateways now tear down finished workers with
`deleteLater()` + short `wait(100)` before draining pending work. This step adds
**minimal** production logging for that new teardown branch only. Existing
queue/coalesce/pending-restart logs (PYPOST-486 / PYPOST-754) are unchanged.

No Prometheus-style metrics — desktop app; CI canary remains the H3 stress test.

## Observability Requirements Analysis

| Area | Assessment |
| --- | --- |
| Key components | `EnvironmentStorageGateway`, `CollectionStorageGateway` |
| Critical path | `_on_worker_finished`: capture → `deleteLater` → short `wait` → pending restart |
| Existing coverage | DEBUG start/queue; INFO pending save/load restart; worker ERR on load/save fail |
| Gap closed here | Short join timed out (`wait` returned false) — silent before this ticket |
| Intentionally not logged | Happy-path finish (every op would spam INFO/DEBUG) |

Critical execution path:

1. Worker emits op completion, then `QThread.finished`.
2. Finish slot captures worker, clears `_worker`, schedules `deleteLater`.
3. Short `wait(100)` joins native post-`finished` cleanup (usually returns immediately).
4. Pending save/load starts a **new** worker (existing INFO events).

## Logging Implementation

### Added Logs

- **EMERG**: N/A
- **ALERT**: N/A
- **CRIT**: N/A
- **ERR**: N/A (load/save failures already logged on workers / presenters)
- **WARNING**:
  - `environment_storage_gateway_worker_finish_wait_timeout` in
    `pypost/core/qt/environment_storage_gateway.py` — short join after
    `finished` did not complete within `_WORKER_FINISH_WAIT_MS`; fields:
    `wait_ms`, `pending_save`, `pending_load` (booleans only).
  - `collection_storage_gateway_worker_finish_wait_timeout` in
    `pypost/core/qt/collection_storage_gateway.py` — same for collection
    gateway; fields: `wait_ms`, `pending_load`.
- **NOTICE**: N/A (Python stdlib has no NOTICE; pending restart stays INFO)
- **INFO**: N/A new (existing `*_pending_*_started` retained)
- **DEBUG**: N/A new (no per-finish DEBUG — would fire on every load/save)

### Log Structure

- Structured logs: yes (`key=value` / `%`-style fields)
- Includes context: yes (wait bound + pending flags only)
- Log levels: WARNING (new); existing DEBUG / INFO / ERROR unchanged
- Large payloads: not logged (no environments, collections, or Qt dumps)

### Rationale

1. PYPOST-823 deferred finish-path instrumentation until H3 product teardown
   landed; this ticket is that change.
2. After a queued `finished` on the GUI thread, `wait(100)` should almost always
   return true immediately. A false return is rare and worth a WARNING — it
   signals native cleanup still running while pending restart may proceed.
3. Logging every successful finish would add noise without improving incident
   response; pending restart already has INFO.
4. No new ERR: wait timeout is advisory hygiene, not an operation failure; load /
   save failures remain on the existing worker/presenter paths.

## Metrics Implementation (if applicable)

### Performance Metrics

None added.

### Business Metrics

None added.

### System Health Metrics

None added.

### Rationale (no production metrics)

Lifecycle hygiene is validated by `tests/test_storage_gateway_h3_stress.py`
(segfault or stranded-completion fingerprint). Desktop packaging has no
Prometheus scrape for gateway finish latency; a counter for wait timeouts would
not be consumed.

## Test-side diagnostics (unchanged)

H3 regression observability remains:

- Stress canary: `tests/test_storage_gateway_h3_stress.py`
- Timeout detail on waits: `gateway_timeout_detail` / PYPOST-828 text
  (`busy=` / `pending=` / `worker_running=`)

No new `caplog` assertions for the WARNING — timeout is expected to be rare in
passing suites; presence of the log line is for field / debug triage.

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

N/A beyond stdlib logging (same as sibling storage-async tickets).

## Validation Results

Validation results:

- [x] WARNING only on wait timeout; fields are compact flags / wait_ms
- [x] Large data structures are not logged
- [x] Existing pending-restart INFO / queue DEBUG retained
- [x] No new metrics (documented as not applicable)
- [x] Happy-path finish not instrumented (avoids over-instrumentation)
- [ ] Metrics available for monitoring — N/A

## Notes

- Symmetry: both gateways share the same WARNING pattern and field style.
- If wait timeouts appear in the wild, raise `_WORKER_FINISH_WAIT_MS` only with
  evidence; do not convert to unbounded GUI `wait()`.
- Step 7 may briefly note the WARNING event names in storage-async dev docs.
