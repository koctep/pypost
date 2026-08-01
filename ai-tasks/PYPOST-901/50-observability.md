# PYPOST-901: Observability Implementation

## Scope

**HARNESS-ONLY.** Optional GUI multi-URL Send scenario under one Mapping stub.
No product runtime logging or metrics. Observability is coverage via existing
agent e2e harness events plus pytest failure diagnostics on settle timeout.

## Observability Requirements Analysis

| Area | Assessment |
| --- | --- |
| Key component | `agent_e2e_http_stub(responses_map)` URL router (PYPOST-868) |
| Critical path | Blank session ready → Mapping install → GET Send → POST Send → panel asserts |
| Production product logging | N/A — test module only |
| Metrics | N/A — pytest harness |

## Logging Implementation

### Added Logs

None new as distinct event names.

Existing events reused by `tests/test_agent_e2e_http_mapping_multi_url.py`:

- **INFO** `agent_e2e_fixture_ready mode=blank` — emitted when
  `agent_e2e_session` packaging reaches UI ready
  (`tests/_pytest_plugins/agent_e2e.py`).
- **INFO** `agent_e2e_http_stub_installed name=url_router` — emitted once when
  `agent_e2e_http_stub(responses)` installs the two-URL Mapping (catalog name
  auto-selected for Mapping installs without explicit `name=`;
  `pypost/fixtures/agent_e2e_http.py`).

On CI / local failure, existing failure-artifact events may also appear:

- **INFO** `agent_e2e_failure_artifacts_written` — snapshot dump succeeded.
- **WARNING** `agent_e2e_failure_artifacts_failed` — dump path failed.

- **EMERG**: none
- **ALERT**: none
- **CRIT**: none
- **ERR**: none (router miss raises `AssertionError` in pytest output, not a
  log line; scenario uses only mapped URLs)
- **WARNING**: none in the happy path; failure-artifact WARNING only on dump
  errors
- **NOTICE**: none
- **INFO**: reuse stub install + fixture ready (above)
- **DEBUG**: none new (per-route URL logging intentionally omitted — PYPOST-868)

### Log Structure

- Structured logs: yes (existing `name=` token on stub install)
- Includes context: catalog name only; no request/response bodies in logs
- Log levels: INFO (install, fixture ready); WARNING/INFO on failure artifacts

### Timeout diagnostics (not log lines)

When Send settle exceeds `SEND_SETTLE_TIMEOUT_S`, `_wait_response` re-raises
`UiWaitTimeoutError` with:

- `step`: `wait_response_after_mapping_get_send` or
  `wait_response_after_mapping_post_send`
- `response_excerpt`: compact panel excerpt from `response_panel_excerpt`
  (same pattern as env GET / seed POST scenarios)

These surface in pytest output and failure artifacts; they are not syslog events.

## Metrics Implementation (if applicable)

### Performance Metrics

None. Send settle cost is bounded by shared `SEND_SETTLE_TIMEOUT_S` (15s per
Send; module timeout 60s).

### Business Metrics

None.

### System Health Metrics

None.

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics — not applicable
- [ ] Grafana dashboards — not applicable
- [ ] Alerting rules — not applicable
- [x] Log aggregation — existing events greppable:
  `agent_e2e_http_stub_installed name=url_router`,
  `agent_e2e_fixture_ready mode=blank`

Catalog: `doc/dev/logging.md` (`agent_e2e_*` table).

## Validation Results

Validation results:

- [x] Logs are correctly formatted (existing stub install + fixture ready)
- [x] Metrics are collected correctly (N/A)
- [x] Logging works for Mapping install (PYPOST-870 caplog proof on golden;
  PYPOST-868 unit tests use `name=url_router` explicitly)
- [x] Large data structures are not logged (no bodies in install event;
  excerpt only on timeout failure)
- [x] Metrics are available for monitoring (N/A)

## Notes

Decision: **no new instrumentation** for this debt story. One Mapping install
log (`name=url_router`) covers both Sends; per-URL route logging would add
noise without improving CI signal.

Authors can confirm stub wrap in test output:

```bash
make test-agent-e2e PYTEST_ARGS='tests/test_agent_e2e_http_mapping_multi_url.py -q -s' \
  2>&1 | grep agent_e2e_http_stub_installed
```

Expected: `agent_e2e_http_stub_installed name=url_router`.
