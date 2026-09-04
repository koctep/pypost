# PYPOST-1256: Observability Implementation

## Logging Implementation

### Added Logs

Lifecycle owners emit one correlated start/completion pair per teardown attempt. The records use
the stable owner category and a generated `teardown_id`; completion records include outcome,
elapsed time, deadline, active work, and pending work. The composition root uses the same ID for
child-owner records and reports the aggregate outcome as `main_window`.

- **INFO**: teardown start/completion, cancellation admission, and safe late-delivery suppression.
- **WARNING**: incomplete/timeout and history persistence failure conditions continue to use the
  existing owner logger contracts.
- **ERROR**: existing history and environment storage failure logs remain available with operation
  context.

The new lifecycle records contain bounded categories and counts only. They do not log request
bodies, URLs, headers, environment values, or storage payloads. Existing `tabs_presenter.logger`
compatibility remains unchanged.

### Log Structure

Log format used:

- Structured logs: yes — key/value fields in the existing syslog-compatible message style.
- Includes context: yes — owner, correlation ID, outcome, deadline, duration, and work counts.
- Log levels: INFO, WARNING, and ERROR.

## Metrics Implementation

The existing Prometheus and OpenTelemetry tracker contracts now expose the same lifecycle
instruments:

- `lifecycle_teardowns_total{owner,outcome}` counts terminal teardown outcomes, including the
  `main_window` aggregate.
- `lifecycle_teardown_duration_seconds{owner,outcome}` records teardown duration.
- `lifecycle_teardown_active_workers{owner}` and `lifecycle_teardown_pending_work{owner}` expose
  the counts observed at teardown admission.
- `lifecycle_events_total{owner,event}` counts cancellation requests, admission rejections, and
  suppressed late signals.
- `environment_update_dispositions_total{disposition}` counts persisted, coalesced, failed,
  incomplete, and post-cutoff-rejected updates.
- `history_io_failures_total{operation}` counts load and save failures.

All metric labels are normalized to fixed allow-lists to prevent unbounded cardinality and avoid
putting request or storage data into telemetry.

## Monitoring Integration

Integration with monitoring systems:

- [x] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [x] Log aggregation (ELK, Loki, etc.) — compatible structured message fields

## Validation Results

Validation results:

- [x] `tests/test_lifecycle_observability.py`: 7 tests passed through `make test`.
- [x] History, request-tabs, environment, and MainWindow teardown logs have correlated
  start/completion coverage; repeated request teardown is verified to be silent and idempotent.
- [x] Late environment delivery is verified to be suppressed without exposing the supplied
  failure text.
- [x] Prometheus lifecycle counters/gauges and all five environment-update dispositions are
  verified with bounded labels.
- [x] OpenTelemetry teardown, event, environment-disposition, and history-I/O instruments are
  verified with bounded labels and non-negative worker counts.
- [x] `make lint`, `make typecheck`, and `make verify-ai-tasks` passed.
- [ ] Focused SOLID audit: four structural checks passed; the protected snapshot comparison
  remains a baseline mismatch because `ai-tasks/PYPOST-376/baseline-metrics.md` is unchanged.
- [ ] Full `make check WORKERS=1`: 332 passed, 6 skipped, and 3 failures. The failures are the
  two known malformed-expression expectations in `tests/test_function_expression_resolver.py`
  and `tests/test_template_service.py`, plus the protected SOLID snapshot comparison in
  `tests/test_solid_audit_baseline.py`; no lifecycle observability test failed.

## Notes

Metrics are optional at owner construction time through the existing no-op tracker, preserving
public behavior for injected test doubles and callers that do not enable telemetry. The request
teardown start record now uses the same owner correlation ID as its terminal record. The protected
`AGENTS.md`, sprint registry, and `ai-tasks/PYPOST-376/baseline-metrics.md` were not changed by
this step.
