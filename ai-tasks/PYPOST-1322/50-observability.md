# PYPOST-1322: Observability Implementation

## Decision

**No new production logging or metrics.** PYPOST-1322 is test-only characterization of
the accepted PYPOST-1264 Risk 3 contract: when `_on_worker_finished` runs nested inside
collection-import teardown wait-for-idle `processEvents`, the join remains uncapped by the
remaining caller budget, overrun is bounded by `worker_finish_join_ms`, and the existing
WARNING fires on stall.

Production already emits `collection_import_worker_finish_wait_timeout`. Requirements and
architecture explicitly forbid new production logging/metrics beyond asserting that warning.
Step 6 therefore documents why observability is N/A for this change set and how the new
characterization test locks the existing diagnostic.

## Observability Requirements Analysis

| Path | Production relevance | Monitoring need |
| --- | --- | --- |
| Nested `_on_worker_finished` join during teardown P1 | Existing production path (unchanged) | Already covered by WARNING `collection_import_worker_finish_wait_timeout wait_ms=%d` |
| Overrun bound ≤ `worker_finish_join_ms` | Existing policy / deadline contract | Characterization asserts via FakeClock + spy waits; no new metric |
| `test_nested_worker_finish_join_overrun_during_wait_idle` | Test harness only | Caplog C1 asserts the existing WARNING; no product telemetry |

Critical execution path for operators remains the existing WARNING on the
`pypost.ui.presenters.collection_import_actions` logger. Adding duplicate or test-only log
lines would not improve production diagnosability and would violate the characterization-only
scope.

## Logging Implementation

### Added Logs

No logging added to production or tests.

- **EMERG**: N/A
- **ALERT**: N/A
- **CRIT**: N/A
- **ERR**: N/A
- **WARNING**: N/A — no new WARNING; existing event asserted (see below)
- **NOTICE**: N/A
- **INFO**: N/A
- **DEBUG**: N/A

### Existing signal covered by this task (unchanged production)

| Level | Event | Location | Role |
| --- | --- | --- | --- |
| WARNING | `collection_import_worker_finish_wait_timeout wait_ms=%d` | `CollectionImportActions._on_worker_finished` in `pypost/ui/presenters/collection_import_actions.py` | Stall after post-`finished` join using full `worker_finish_join_ms` (not deadline-bounded; Risk 3) |

Characterization coverage:

- Test: `tests/test_collection_import_teardown_policy.py::test_nested_worker_finish_join_overrun_during_wait_idle`
- Caplog contract C1: `caplog.at_level(logging.WARNING, logger=…collection_import_actions)` and
  match `collection_import_worker_finish_wait_timeout wait_ms=<join_ms>`

Documented for operators in `doc/dev/collection_import.md` (troubleshooting /
shared-deadline exceptions). Prior tickets that introduced or catalogued this event include
PYPOST-1005 / PYPOST-1058 / PYPOST-1059 / PYPOST-1148 / PYPOST-1264 / PYPOST-1265.

### Why not add new logs

- Production already surfaces the stall path with a structured, greppable WARNING.
- Requirements Definition of Done item 4 and non-functional requirements forbid intentional
  production warning/text changes and state no new production logging is required beyond
  asserting the existing warning.
- Test-helper / nesting-hook logging would add CI noise without a production consumer.

### Log Structure

- Structured logs: N/A for new events; existing WARNING uses `key=value` (`wait_ms`)
- Includes context: existing event includes `wait_ms` (join allowance used)
- Log levels: N/A for additions; covered event is WARNING

## Metrics Implementation (if applicable)

### Performance Metrics

- **Response time**: N/A
- **Throughput**: N/A
- **Error rate**: N/A — stall diagnosability is log-based, not a Prometheus series

### Business Metrics

- N/A — no product import/teardown behavior change

### System Health Metrics

- **Resource usage**: N/A
- **Component status**: N/A

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics (N/A — desktop app; no new series)
- [ ] Grafana dashboards (N/A)
- [ ] Alerting rules (N/A — operators rely on existing WARNING in app logs)
- [ ] Log aggregation (ELK, Loki, etc.) (N/A for this task; existing WARNING remains greppable)

## Validation Results

Validation results:

- [x] No new production logs or metrics required for this change set
- [x] Existing WARNING `collection_import_worker_finish_wait_timeout` remains the Risk 3
  diagnostic (source: `_on_worker_finished`; asserted by characterization test)
- [x] Large data structures are not logged (no logging added)
- [ ] Metrics are collected correctly (N/A)
- [ ] Metrics are available for monitoring (N/A)
- [x] Caplog characterization covers nested stall path (Step 4 green; no Step 6 code change)

## Notes

- This step changes task documentation only (`50-observability.md` + roadmap Step 6 notes).
- No `pypost/`, `tests/`, or Makefile edits in Step 6.
- Outcome: **N/A — no new observability; existing WARNING covered by characterization test.**
