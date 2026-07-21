# PYPOST-871: Observability Implementation

## Logging Implementation

### Added Logs

None new. The scenario uses the existing shared HTTP stub install event
from PYPOST-859:

- **INFO** `agent_e2e_http_stub_installed name=seed_post_ok` — emitted when
  `stub_agent_e2e_http` / `agent_e2e_http_stub` installs
  `CANNED_SEED_POST_OK` (catalog identity auto-name).

No product runtime logging added (test-only story).

- **EMERG**: none
- **ALERT**: none
- **CRIT**: none
- **ERR**: none
- **WARNING**: none
- **NOTICE**: none
- **INFO**: reuse existing stub install event (above)
- **DEBUG**: none new

Existing agent e2e events remain unchanged
(`agent_e2e_fixture_ready`, `agent_e2e_http_stub_installed`,
`agent_e2e_failure_artifacts_*`, `ui_snapshot_captured`).

### Log Structure

- Structured logs: yes (existing stub event `name=<catalog>`)
- Includes context: catalog name only (no request body in logs)
- Levels: INFO (existing)

Scenario intentionally does not log request/response bodies; wait
timeout diagnostics carry step context only.

## Metrics Implementation (if applicable)

### Performance Metrics

None. Send settle cost matches env GET / golden (15s bounded wait).

### Business Metrics

None.

### System Health Metrics

None.

## Monitoring Integration

- [ ] Prometheus metrics — not applicable
- [ ] Grafana dashboards — not applicable
- [ ] Alerting rules — not applicable
- [x] Log aggregation — existing `agent_e2e_http_stub_installed` greppable
  for `name=seed_post_ok`

## Validation Results

- [x] Stub install log already correct for catalog identity
- [x] No large structures logged by this scenario
- [x] Metrics N/A
- [x] Caplog proof for stub install remains optional sibling
  ([PYPOST-870](https://pypost.atlassian.net/browse/PYPOST-870))

## Notes

Observability for this debt is coverage via an existing event, not new
instrumentation. Authors can confirm stub wrap with
`grep agent_e2e_http_stub_installed` / `name=seed_post_ok`.
