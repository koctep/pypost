# PYPOST-903: Observability Implementation

## Scope

**TEST-ONLY.** This task expands caplog coverage for the existing HTTP stub
install event. **No new production logging or metrics** — all `name=` tokens are
already emitted by `stub_agent_e2e_http` (PYPOST-859 / PYPOST-868).

## Observability Requirements Analysis

| Area | Assessment |
| --- | --- |
| Key component | `stub_agent_e2e_http` in `pypost/fixtures/agent_e2e_http` |
| Critical path | Stub CM enter → INFO `agent_e2e_http_stub_installed` |
| Production logging gap | None |
| Production metrics gap | N/A |
| Test harness | Parametrized caplog matrix (6 install name tokens) |

## Logging Implementation

### Added Logs

None new in production.

Verified by expanded test matrix:

- **INFO**: catalog tokens — `golden_ok`, `seed_get_ok`, `seed_post_ok`,
  `double_body_lock_ok`
- **INFO**: Mapping default — `url_router`
- **INFO**: explicit override — `scenario_alpha` (custom `name=`)

### Log Structure

- Structured logs: yes (event prefix + `name=` token)
- Includes context: yes (`name=` catalog / custom / `url_router`)
- Log levels: INFO (install)

## Metrics Implementation (if applicable)

N/A — no new metrics.

## Monitoring Integration

- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

Not applicable. Developers grep `agent_e2e_http_stub_installed` in CI logs;
catalog in `doc/dev/logging.md`.

## Validation Results

Validation results:
- [x] Logs are correctly formatted (existing event prefixes)
- [x] Metrics are collected correctly (N/A)
- [x] Logging works in install scenarios (6 parametrized rows)
- [x] Large data structures are not logged
- [x] Metrics are available for monitoring (N/A)

## Notes

Caplog proof pattern unchanged from PYPOST-870:
`caplog.at_level(logging.INFO, logger="pypost.fixtures.agent_e2e_http")`
plus substring assert on `agent_e2e_http_stub_installed name=<token>`.
