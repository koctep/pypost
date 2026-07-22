# PYPOST-870: Observability Implementation

## Scope

**TEST-ONLY.** This task adds caplog coverage for the existing HTTP stub
install event. **No new production logging or metrics** were required —
`agent_e2e_http_stub_installed name=<…>` already landed in PYPOST-859 and
is cataloged in `doc/dev/logging.md`.

## Observability Requirements Analysis

| Area | Assessment |
| --- | --- |
| Key component | `stub_agent_e2e_http` in `pypost.fixtures.agent_e2e_http` |
| Critical path | Stub CM enter → INFO `agent_e2e_http_stub_installed` |
| Production logging gap | None (already implemented) |
| Production metrics gap | N/A — pytest harness path; no new counters |
| Test harness | Caplog INFO assertion for golden_ok install |

## Logging Implementation

### Added Logs

None new in production.

Existing (verified by new test):

- **INFO**: `pypost/fixtures/agent_e2e_http.py` —
  `agent_e2e_http_stub_installed name=golden_ok` when
  `stub_agent_e2e_http(CANNED_GOLDEN_OK)` is entered

### Log Structure

- Structured logs: yes (event prefix + `name=` token)
- Includes context: yes (`name=` catalog / custom / `url_router`)
- Log levels: INFO (install)

## Metrics Implementation (if applicable)

### Performance Metrics

N/A — no new metrics for this debt item.

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

Not applicable for this local pytest harness debt. Developers grep
`agent_e2e_http_stub_installed` in CI/agent logs; catalog remains in
`doc/dev/logging.md`.

## Validation Results

Validation results:
- [x] Logs are correctly formatted (existing event prefixes)
- [x] Metrics are collected correctly (N/A)
- [x] Logging works in install scenarios
  (`test_stub_agent_e2e_http_logs_installed_event`)
- [x] Large data structures are not logged
- [x] Metrics are available for monitoring (N/A)

## Notes

Caplog proof (INFO path, not ERROR C1):
`caplog.at_level(logging.INFO, logger="pypost.fixtures.agent_e2e_http")`
plus `"agent_e2e_http_stub_installed name=golden_ok" in caplog.text`.
No allowlist change needed (INFO, not ERROR).
