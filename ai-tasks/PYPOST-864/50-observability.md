# PYPOST-864: Observability Implementation

## Scope

**TEST-ONLY.** This task adds a code↔doc inventory drift guard. **No new
production logging or metrics** were required — seed write events remain
those from PYPOST-857 (`agent_e2e_seed_completed` /
`agent_e2e_seed_failed`).

## Observability Requirements Analysis

| Area | Assessment |
| --- | --- |
| Key component | Seed inventory constants vs `doc/dev/agent_e2e_seed.md` |
| Critical path | CI fails when a published `SEED_*` token is missing from the doc |
| Production logging gap | None |
| Production metrics gap | N/A — pytest unit guard only |
| Test harness | Assertion messages name missing `const_name=token` |

## Logging Implementation

### Added Logs

None new in production.

### Log Structure

N/A — no production log changes.

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

Not applicable. Drift surfaces as a failing pytest assertion in CI /
`make test`.

## Validation Results

Validation results:
- [x] Logs are correctly formatted (N/A)
- [x] Metrics are collected correctly (N/A)
- [x] Logging works in error scenarios (N/A — assert message on drift)
- [x] Large data structures are not logged
- [x] Metrics are available for monitoring (N/A)

## Notes

Failure signal is the pytest assertion text:
`missing inventory token for {const_name}={token!r}` against
`doc/dev/agent_e2e_seed.md`.
