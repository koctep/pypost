# PYPOST-1421: Observability Implementation

## Logging Implementation

### Scope and Context

This ticket deepens the **boolean readiness gate** inside
`tests/helpers/shared_venv_manager.py` (`SharedVenvManager.is_ready` /
`_prewarmed_base_pth_target_ok`). That helper remains **test harness
infrastructure**, not a deployed production service under `pypost/`.

Per repository test standards and continuity with PYPOST-1419 / PYPOST-1420,
fixture helpers must avoid uncontrolled root-logger / `sys.stderr` noise on the
healthy path. Deep readiness is intentionally a silent fail-closed predicate:
callers (`ensure_ready`, `materialize`, `_venv_ready`) already react by
rebuilding the skeleton or falling back to the shared base, and materialize
failures still raise stage-aware `RuntimeError` messages from PYPOST-1420.

No `logging` / OpenTelemetry / Prometheus instrumentation was added for this
boolean gate.

### Added Logs

Mapped syslog-compatible levels to diagnostic surfaces:

- **EMERG**: N/A — Test harness does not manage host/kernel emergencies.
- **ALERT**: N/A — Test harness does not own operator paging.
- **CRIT**: N/A — Critical production alerts do not apply to local/CI fixtures.
- **ERR**: Unchanged from prior tickets — materialize / bootstrap
  `RuntimeError` paths remain the fail-loud surface when population or
  preparation fails after readiness rejects a damaged template. Readiness
  itself does not raise; it returns `False`.
- **WARNING**: N/A — No soft-degraded “accept damaged `.pth`” path; damage
  fails closed via `is_ready == False`.
- **NOTICE**: N/A — Readiness remains on-disk markers + deep `.pth` validation
  state, not notice-level logs.
- **INFO**: N/A — Healthy readiness checks are silent by design (avoid pytest
  log noise). Success is observable via ready markers, green suites, and
  rebuilt skeletons after `ensure_ready`.
- **DEBUG**: N/A for the predicate. Nested causes on materialize/bootstrap
  failures remain available via exception chaining from prior tickets.

### Log Structure

Log format used:
- Structured logs: Yes for existing materialize/bootstrap errors (target /
  source / budget fields). Readiness returns a boolean only.
- Includes context: Yes on failure paths that already exist; deep readiness
  does not emit new free-form text.
- Log levels: Exception-equivalent `ERR` on materialize/bootstrap only.
- Sanitization: `.pth` contents and full site-packages trees are **not**
  dumped by readiness.

## Metrics Implementation (if applicable)

### Performance Metrics

No production metrics exporters were added. Harness/test telemetry remains:

- **Response time**: Parallel wall-clock covered by
  `tests/test_makefile_shared_readiness.py::test_parallel_workspace_materialization_under_load_budget`
  (must stay within budget when templates are healthy).
- **Throughput**: Unchanged; rejecting damaged templates avoids copying a
  broken skeleton that would force slower recovery.
- **Error rate**: Exercised by unit cases that assert `is_ready` is False for
  missing/invalid `.pth` targets.

### Business Metrics

Business metrics:
- N/A for harness-only change.

### System Health Metrics

System health metrics:
- **Component status**: `is_ready` / `_venv_ready` + on-disk
  `.initialized-*` markers and validated `_prewarmed_base.pth` target
  directory readability.
- **Resource usage**: N/A — no new collectors.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

N/A — test harness only; CI observes failures via pytest / Make exit codes.

## Validation Results

Validation results:
- [x] No new healthy-path log noise introduced
- [x] Existing materialize/bootstrap ERR diagnostics retained
- [x] Deep readiness fail-closed behavior covered by unit tests
- [x] Large data structures are not logged
- [x] Metrics remain harness/assertion based (load-budget suite)

## Notes

- A dedicated “template damaged” warning/error string was explicitly deferred
  (requirements Q&A / architecture). If operators need a louder CI signal
  without relying on rebuild/fallback side effects, record it as follow-up
  debt in Step 7.
