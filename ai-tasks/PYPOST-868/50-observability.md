# PYPOST-868: Observability Implementation

## Scope

**HARNESS-ONLY.** Reuses existing install INFO
`agent_e2e_http_stub_installed`. Mapping installs default to
`name=url_router` when callers leave `name=` at `custom`. No new metrics;
no per-route DEBUG spam (would drown agent e2e logs).

## Observability Requirements Analysis

| Area | Assessment |
| --- | --- |
| Key component | `stub_agent_e2e_http` / URL router side_effect |
| Critical path | Stub install → Send routed by URL → miss AssertionError |
| Production product logging | N/A — fixture module only |
| Metrics | N/A — pytest harness |

## Logging Implementation

### Added Logs

None new as distinct event names.

Existing (extended naming):

- **INFO**: `pypost/fixtures/agent_e2e_http.py` —
  `agent_e2e_http_stub_installed name=url_router` when a Mapping is
  installed without an explicit `name=` override (or `name=url_router`
  when passed explicitly).

Miss path uses `AssertionError` text (not a log line) so failures surface
in pytest output with `url=` and `known=`.

### Log Structure

- Structured logs: yes (`agent_e2e_http_stub_installed` + `name=`)
- Includes context: yes (`name` token)
- Log levels: INFO (install)

## Metrics Implementation (if applicable)

### Performance Metrics

N/A

### Business Metrics

N/A

### System Health Metrics

N/A

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

Not applicable for local pytest harness. Catalog entry remains in
`doc/dev/logging.md` (`agent_e2e_http_stub_installed`).

## Validation Results

Validation results:
- [x] Logs are correctly formatted (existing event + `url_router` name)
- [x] Metrics are collected correctly (N/A)
- [x] Logging works for Mapping install (unit tests capture INFO)
- [x] Large data structures are not logged (no response bodies in install)
- [x] Metrics are available for monitoring (N/A)

## Notes

Decision: do not log every routed URL at INFO — install once is enough;
misses fail the test via AssertionError.
