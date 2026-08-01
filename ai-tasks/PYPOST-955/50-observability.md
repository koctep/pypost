# PYPOST-955: Observability Implementation

## Scope

**TEST-ONLY.** Timeout companion coverage for mapping multi-URL Send settle
diagnostics. No new production logging or metrics.

Timeout rewrap with stable `step` names and `response_excerpt` is **defined by
[PYPOST-901](https://pypost.atlassian.net/browse/PYPOST-901)** in
`ai-tasks/PYPOST-901/50-observability.md` and implemented in
`tests/test_agent_e2e_http_mapping_multi_url.py` (`_wait_response`). This task
adds an automated companion that **asserts** that contract on a forced timeout —
not new instrumentation.

## Observability Requirements Analysis

| Area | Assessment |
| --- | --- |
| Key component | Mapping multi-URL Send settle (`wait_for_snapshot` predicate) |
| Critical path | Forced near-zero settle → `UiWaitTimeoutError` rewrap → pytest asserts |
| Production product logging | N/A — companion test only |
| Metrics | N/A — pytest harness |
| Parent contract | PYPOST-901 timeout diagnostics (`step`, `response_excerpt`) |

## Logging Implementation

### Added Logs

None. Reuse existing harness events from the PYPOST-901 mapping module family:

- **INFO** `agent_e2e_fixture_ready mode=blank` — session packaging ready
  (`tests/_pytest_plugins/agent_e2e.py`).
- **INFO** `agent_e2e_http_stub_installed name=url_router` — Mapping stub install
  (`pypost/fixtures/agent_e2e_http.py`).

On CI failure, existing failure-artifact events may appear (unchanged):

- **INFO** `agent_e2e_failure_artifacts_written`
- **WARNING** `agent_e2e_failure_artifacts_failed`

- **EMERG**: none
- **ALERT**: none
- **CRIT**: none
- **ERR**: none (forced timeout is caught by companion; not a log line)
- **WARNING**: failure-artifact WARNING only on dump errors
- **NOTICE**: none
- **INFO**: reuse fixture ready + stub install (above)
- **DEBUG**: none new

### Log Structure

- Structured logs: yes (existing `name=` token on stub install)
- Includes context: catalog name only; no request/response bodies in logs
- Log levels: INFO (install, fixture ready); WARNING/INFO on failure artifacts

## Harness observability (test path)

The companion
`test_mapping_get_send_settle_timeout_includes_step_and_excerpt` exercises the
PYPOST-901 diagnostic carrier on a forced mapping GET Send settle timeout:

| Field | Source | Purpose |
| --- | --- | --- |
| `step` | Inline rewrap (mirrors `_wait_response`) | `wait_response_after_mapping_get_send` triage fingerprint |
| `response_excerpt` | `response_panel_excerpt(session.ui_snapshot())` | Compact panel context at timeout |

Forced timeout uses an impossible snapshot predicate (`lambda _: False`) with
`FORCED_SETTLE_TIMEOUT_S` (0.05s) — same wall-clock intent as golden/dialog
timeout companions (PYPOST-950 / 934). The companion inlines rewrap rather than
calling `_wait_response` (which uses 15s `SEND_SETTLE_TIMEOUT_S`).

POST step name `wait_response_after_mapping_post_send` remains covered by the
parent PYPOST-901 `_wait_response` implementation and observability contract;
this companion locks the GET path plus excerpt assertion per Jira acceptance.

These fields surface in `UiWaitTimeoutError.diagnostics` and pytest output — not
syslog events. See parent doc:
`ai-tasks/PYPOST-901/50-observability.md` (Timeout diagnostics section).

## Metrics Implementation (if applicable)

### Performance Metrics

None. Module wall-clock bound by `pytest.mark.timeout(60)` on the mapping module.

### Business Metrics

None.

### System Health Metrics

None.

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics — not applicable
- [ ] Grafana dashboards — not applicable
- [ ] Alerting rules — not applicable
- [x] Log aggregation — existing events greppable (unchanged from PYPOST-901):
  `agent_e2e_http_stub_installed name=url_router`,
  `agent_e2e_fixture_ready mode=blank`

Catalog: `doc/dev/logging.md` (`agent_e2e_*` table).

## Validation Results

Validation results:

- [x] Logs are correctly formatted (no new events; existing stub install +
  fixture ready)
- [x] Metrics are collected correctly (N/A)
- [x] Companion asserts `step` and `response_excerpt` on forced timeout
- [x] Large data structures are not logged (excerpt only on failure path)
- [x] Metrics are available for monitoring (N/A)

Verification:

```bash
make test-agent-e2e PYTEST_ARGS='tests/test_agent_e2e_http_mapping_multi_url.py::test_mapping_get_send_settle_timeout_includes_step_and_excerpt -q'
```

Inventory gate (Step 3) remains in `tests/test_agent_e2e_http.py`:

```bash
make test-agent-e2e PYTEST_ARGS='tests/test_agent_e2e_http.py::test_mapping_multi_url_settle_timeout_companion_exists -q'
```

## Notes

Decision: **no new production instrumentation.** Observability for PYPOST-955 is
automated proof that PYPOST-901 timeout diagnostics remain stable — parity with
the golden Send timeout companion pattern (PYPOST-950) at the assertion layer
only.

Deliberately not added (out of scope per requirements):

- Caplog proof for `name=url_router` — tracked as PYPOST-957 debt
- POST-path forced-timeout companion — GET path satisfies acceptance; POST step
  name documented in parent contract
- Per-route DEBUG logging — noise without CI signal (PYPOST-901 decision)

## Worklog

tokens_used: (subagent aggregate)
role: execution
step: 6
step_name: observability
