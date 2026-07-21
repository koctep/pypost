# PYPOST-859: Observability Implementation

## Logging Implementation

### Added Logs

HTTP fixture layer is a test stub. Lifecycle / packaging / seed events
already cover session bootstrap. This story adds one install-boundary
event so authors can grep that the **shared** stub (not a private patch)
was activated.

- **EMERG**: none
- **ALERT**: none
- **CRIT**: none
- **ERR**: none new — transport errors remain product `HTTPClient` /
  worker paths when not stubbed
- **WARNING**: none new
- **NOTICE**: none (stdlib logging has no NOTICE; use INFO)
- **INFO**:
  - `pypost.fixtures.agent_e2e_http` —
    `agent_e2e_http_stub_installed name=<catalog_or_custom>` when
    `stub_agent_e2e_http` enters (known catalog identities map to
    `golden_ok` / `seed_get_ok` / `seed_post_ok`)
- **DEBUG**: none — install INFO is enough for harness grepping

Scalars only (`name`); no URLs, bodies, headers, or result payloads.

### Log Structure

Log format used:
- Structured logs: yes (`event_name key=value` per `doc/dev/logging.md`)
- Includes context: yes (`name=…`)
- Log levels: INFO (stub install); compose with
  `agent_e2e_fixture_ready` / `agent_session_*`

## Metrics Implementation (if applicable)

### Performance Metrics

None. Stub install cost is negligible; Send settle remains visible via
`ui_wait_*` / pytest duration plugin. No Prometheus instruments for test
HTTP stubs.

### Business Metrics

None.

### System Health Metrics

None new. Failures remain assertion / wait-timeout carriers from agent
primitives.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics — not applicable for pytest HTTP stubs
- [ ] Grafana dashboards — not applicable
- [ ] Alerting rules — not applicable
- [x] Log aggregation — `agent_e2e_http_stub_installed` follows project
  `event_name key=value` convention
- [x] CI / test gate — `make test-agent-e2e` includes golden + env Send

## Validation Results

Validation results:
- [x] Logs use structured event names consistent with project
- [x] Large data structures are not logged
- [x] Install event fires when stub context enters
- [x] `make test-agent-e2e` → 32 passed with logging present
- [x] Catalog entry in `doc/dev/logging.md` — Step 7 (Dev Docs)

## Notes

- Authors diagnosing Send determinism should grep
  `agent_e2e_http_stub_installed` then `ui_action_applied` /
  `ui_wait_settled`.
- Private `unittest.mock.patch` of `send_request` outside this helper
  will **not** emit the event (by design — prefer the shared layer).
