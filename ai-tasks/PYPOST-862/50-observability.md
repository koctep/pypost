# PYPOST-862: Observability Implementation

## Scope

**TEST-ONLY.** This task adds caplog coverage for the existing seed write
failure path. **No new production logging or metrics** were required —
`agent_e2e_seed_failed` / `agent_e2e_seed_completed` already landed in
PYPOST-857 and are cataloged in `doc/dev/logging.md`.

## Observability Requirements Analysis

| Area | Assessment |
| --- | --- |
| Key component | `write_agent_e2e_seed` in `pypost.fixtures.agent_e2e_seed` |
| Critical path | Persist failure → ERROR log → re-raise |
| Production logging gap | None (already implemented) |
| Production metrics gap | N/A — desktop harness path; no new counters |
| Test harness | Caplog C1 assertion for ERROR event |

## Logging Implementation

### Added Logs

None new in production.

Existing (verified by new test):

- **ERR**: `pypost/fixtures/agent_e2e_seed.py` —
  `agent_e2e_seed_failed data_dir=%s` via `logger.exception`, then re-raise
- **INFO**: `agent_e2e_seed_completed` (success path; covered elsewhere)

### Log Structure

- Structured logs: yes (event prefix + `data_dir`; exception via
  `logger.exception`)
- Includes context: yes (`data_dir`, traceback)
- Log levels: ERROR (failure), INFO (success)

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
`agent_e2e_seed_failed` in CI/agent logs; catalog remains in
`doc/dev/logging.md`.

## Validation Results

Validation results:
- [x] Logs are correctly formatted (existing event prefix)
- [x] Metrics are collected correctly (N/A)
- [x] Logging works in error scenarios
  (`test_write_agent_e2e_seed_logs_failure_and_reraises`)
- [x] Large data structures are not logged
- [x] Metrics are available for monitoring (N/A)

## Notes

Caplog contract (do-testing C1):
`caplog.at_level(logging.ERROR, logger="pypost.fixtures.agent_e2e_seed")`
plus `"agent_e2e_seed_failed" in caplog.text`. No allowlist change needed.
