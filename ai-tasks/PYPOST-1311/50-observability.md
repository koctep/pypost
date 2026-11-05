# PYPOST-1311: Observability Implementation

## Summary

No new production logging or metrics. PYPOST-1311 is a **test-only** fix: the Step 3
repro and the named e2e scenario call existing `EnvPresenter.wait_storage_idle(...)`
and `EnvPresenter.teardown(...)` before `TemporaryDirectory` cleanup. `pypost/` is
unchanged for this task.

Existing async-storage and lifecycle instrumentation already covers the paths these
tests exercise. Adding duplicate prod signals for a harness fence would not improve
operator diagnostics.

## Logging Implementation

### Added Logs

None. No production log lines were added, changed, or removed.

- **EMERG**: N/A — no production code change.
- **ALERT**: N/A — no production code change.
- **CRIT**: N/A — no production code change.
- **ERR**: N/A — no production code change.
- **WARNING**: N/A — no production code change.
- **NOTICE**: N/A — no production code change.
- **INFO**: N/A — no production code change.
- **DEBUG**: N/A — no production code change.

### Existing Logs Covering This Scenario

When the fenced tests call `load_environments()` with encryption enabled, then
`wait_storage_idle`, then `teardown`, the following **already-present** events apply
(from prior tasks such as PYPOST-486 / lifecycle teardown work). Operators and CI
caplog consumers can correlate async load → idle wait → teardown without new events.

| Level | Event | Location | Relevance to PYPOST-1311 |
| --- | --- | --- | --- |
| INFO | `environment_storage_async_load_dispatched` | `pypost/ui/presenters/env_presenter.py` `load_environments` | Marks encrypted async load handoff to the gateway — the in-flight work that raced temp-dir cleanup before the test fence. |
| INFO | `environment_storage_gateway_wait_idle_started` | `pypost/core/qt/environment_storage_gateway.py` `wait_idle` | Emitted when `wait_storage_idle` finds pending gateway work (test fence settle step). |
| INFO | `environment_storage_gateway_wait_idle_completed elapsed_ms=%d` | same | Idle succeeded within budget; safe for product asserts / teardown. |
| WARNING | `environment_storage_gateway_wait_idle_timeout elapsed_ms=%d` | same | Idle budget exhausted; tests assert True on wait so this path fails the test rather than leaving files for cleanup. |
| INFO | `lifecycle_teardown_started owner=env_presenter teardown_id=%s timeout_ms=%d` | `pypost/ui/presenters/env_presenter_lifecycle.py` `teardown` | Presenter fence / drain begin (test `finally` / post-assert teardown). |
| INFO | `lifecycle_teardown_completed owner=env_presenter … outcome=%s …` | same | Bounded drain finished; gateway workers should no longer own the temp workspace. |
| INFO | `environment_load_rejected reason=teardown` | `env_presenter.py` | Late load admission cut off after teardown started. |
| INFO | `environment_storage_load_rejected reason=teardown` | `environment_storage_gateway.py` | Gateway-side admission reject after `begin_teardown`. |
| DEBUG | `environment_storage_worker_run_started op=load` | `pypost/core/qt/environment_storage_worker.py` | Worker thread started for the encrypted load. |
| ERROR | `environment_storage_worker_load_failed` / presenter `storage_load_failed` | worker / presenter lifecycle | Missing-key / decrypt failure path that the e2e product assert still covers after idle. |

Related exit-path product log (unchanged, not added by this task):
`main_window_exit_storage_idle` on the real app shutdown path
(`doc/dev/logging.md`).

### Log Structure

- Structured logs: yes (`event_name` + optional `key=value`; existing convention)
- Includes context: yes (`elapsed_ms`, `timeout_ms`, `teardown_id`, `outcome`, counts;
  no secrets, keys, or encrypted envelopes)
- Log levels used on this path: DEBUG, INFO, WARNING, ERROR
- New levels introduced this task: none

## Metrics Implementation (if applicable)

### Performance Metrics

No new metrics. Existing lifecycle teardown metrics continue to record when tests (or
production) call `EnvPresenter.teardown`:

- `lifecycle_teardowns_total{owner,outcome}`
- `lifecycle_teardown_duration_seconds{owner,outcome}`
- `lifecycle_teardown_active_workers{owner}`
- `lifecycle_teardown_pending_work{owner}`

(`pypost/core/metrics_registry.py` via `record_teardown_metrics` in env presenter
lifecycle.)

### Business Metrics

N/A — test harness fence only; no business counters added.

### System Health Metrics

N/A — no new health gauges. Gateway wait-idle timeout remains a WARNING log, not a
new metric series.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics — no new series; existing lifecycle teardown metrics unchanged
- [ ] Grafana dashboards — N/A for this task
- [ ] Alerting rules — N/A for this task
- [ ] Log aggregation (ELK, Loki, etc.) — N/A; existing event names remain greppable

## Validation Results

Validation results:
- [x] Logs are correctly formatted — existing events reviewed in presenter / gateway /
  lifecycle; no new log strings introduced
- [x] Metrics are collected correctly — no new metrics; teardown metrics path untouched
- [x] Logging works in error scenarios — wait-idle timeout WARNING and worker/presenter
  load-failed ERROR paths already exist for stuck or failed async loads
- [x] Large data structures are not logged — dispatch / idle / teardown events carry
  counts and timing only
- [x] Metrics are available for monitoring — pre-existing lifecycle teardown registry
  entries remain

## Notes

**Why no new production instrumentation:** The defect was a test lifecycle race
(temp-dir `rmtree` while an encrypted async load worker still wrote the workspace).
The fix is ordering in tests (`wait_storage_idle` then `teardown` before fixture
exit). Production already exposes:

1. Dispatch visibility (`environment_storage_async_load_dispatched`)
2. Idle wait progress / timeout (`environment_storage_gateway_wait_idle_*`)
3. Bounded teardown start/complete + Prometheus lifecycle teardown metrics

Instrumenting pytest helpers or duplicating those events in test-only wrappers would
not change production observability. Operators diagnosing real async-load or shutdown
issues should continue to use the catalog in `doc/dev/environment_storage_async.md`
and `doc/dev/logging.md`.
