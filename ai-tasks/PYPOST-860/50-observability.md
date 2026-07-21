# PYPOST-860: Observability Implementation

## Logging Implementation

### Added Logs

Failure dumps are a pytest diagnostics path. Events stay scalar-only so
CI logs never print the UI tree or secret values.

- **EMERG**: none
- **ALERT**: none
- **CRIT**: none
- **ERR**: none
- **WARNING**:
  - `pypost.fixtures.agent_e2e_failure` —
    `agent_e2e_failure_artifacts_failed nodeid=… error=<ExcType>` when
    capture or I/O fails (best-effort; original test failure stands)
- **NOTICE**: none (stdlib logging has no NOTICE; use INFO)
- **INFO**:
  - `pypost.fixtures.agent_e2e_failure` —
    `agent_e2e_failure_artifacts_written path=… nodeid=…` after a
    successful dump
- **DEBUG**: none new — snapshot capture still emits
  `ui_snapshot_captured` (PYPOST-835) with counts only

Never log: snapshot tree, node values, `env_vars`, `hidden_keys`, or
full exception payloads beyond type name in the failed-dump WARNING.

### Log Structure

- Structured logs: yes (`event_name key=value` per `doc/dev/logging.md`)
- Includes context: yes (`path`, `nodeid`, `error`)
- Levels: INFO (success), WARNING (dump failure)

## Metrics Implementation (if applicable)

### Performance Metrics

None. Dump cost is dominated by one `ui_snapshot()` walk on failure only;
success paths are unchanged. No Prometheus instruments for test dumps.

### Business Metrics

None.

### System Health Metrics

None new. Primary signal remains the pytest failure plus on-disk
artifacts.

## Monitoring Integration

- [ ] Prometheus metrics — not applicable for pytest failure dumps
- [ ] Grafana dashboards — not applicable
- [ ] Alerting rules — not applicable
- [x] Log aggregation — INFO/WARNING events follow project convention
- [x] CI / test gate — covered by `make test-agent-e2e` / failure artifact
  tests

## Validation Results

- [x] Success dump logs path + nodeid only
- [x] Failed dump logs WARNING without raising
- [x] Snapshot file uses masked `ui_snapshot` values (test proves secret
  absent from JSON)
- [x] Catalog entries added in Step 7 (`doc/dev/logging.md`)

## Notes

- Authors: grep `agent_e2e_failure_artifacts_written` in pytest output,
  then open `path` from the log line.
- Optional CI upload of `artifacts/agent_e2e/` is docs guidance, not a
  metric.
