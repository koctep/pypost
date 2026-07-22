# PYPOST-865: Observability Implementation

## Scope

**TEST CONFIG ONLY.** This task enables pytest `--strict-markers` in
`pyproject.toml` `addopts` and locks the policy with a config guard test.
**No product runtime logging or metrics** were required or added.

## Observability Requirements Analysis

| Area | Assessment |
| --- | --- |
| Key component | `[tool.pytest.ini_options]` `addopts` + markers registry |
| Critical path | Collection fails loudly on unknown custom markers |
| Production logging gap | None — no product code paths changed |
| Production metrics gap | N/A — pytest config / CI hygiene only |
| Failure signal | Pytest unknown-marker error; guard assert on missing flag |

## Logging Implementation

### Added Logs

None. Product and harness loggers are unchanged.

- **EMERG**: N/A
- **ALERT**: N/A
- **CRIT**: N/A
- **ERR**: N/A
- **WARNING**: N/A
- **NOTICE**: N/A
- **INFO**: N/A
- **DEBUG**: N/A

### Log Structure

N/A — no production or harness log changes.

## Metrics Implementation (if applicable)

### Performance Metrics

N/A — strict-markers is a collection-time config flag; no new timers or
throughput instruments.

### Business Metrics

N/A — marker policy enforcement is a pytest CLI concern, not a scrapeable
product counter.

### System Health Metrics

N/A

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

Not applicable. Unknown markers surface as pytest collection failures in
local `make test` / CI. Policy drift (missing `--strict-markers` in
`addopts`) surfaces via `tests/test_pytest_strict_markers.py`.

## Validation Results

Validation results:
- [x] Logs are correctly formatted (N/A — none added)
- [x] Metrics are collected correctly (N/A — none added)
- [x] Logging works in error scenarios (N/A — pytest error text on
  unknown markers)
- [x] Large data structures are not logged
- [x] Metrics are available for monitoring (N/A)

## Notes

- Observability for this debt is CI / pytest failure output, not runtime
  telemetry.
- Authors registering a new custom mark must add it to
  `[tool.pytest.ini_options]` `markers` or collection will fail under
  `--strict-markers`.
