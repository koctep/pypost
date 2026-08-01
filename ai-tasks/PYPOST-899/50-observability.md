# PYPOST-899: Observability Implementation

## Scope

**TEST-ONLY.** This task adds live-session caplog coverage for existing
packaging ready events. **No new production logging or metrics** were required —
`agent_e2e_fixture_ready mode=blank|seeded` already landed in PYPOST-858.

## Observability Requirements Analysis

| Area | Assessment |
| --- | --- |
| Key component | Packaging fixtures in `tests._pytest_plugins.agent_e2e` |
| Critical path | Live session ready → INFO `agent_e2e_fixture_ready` |
| Production logging gap | None (already implemented) |
| Production metrics gap | N/A — pytest harness path |
| Test harness | Live caplog INFO assertion for blank + seeded modes |

## Logging Implementation

### Added Logs

None new in production.

Existing (verified by new live smokes):

- **INFO**: `tests/_pytest_plugins/agent_e2e.py` —
  `agent_e2e_fixture_ready mode=blank` after blank session ready
- **INFO**: `tests/_pytest_plugins/agent_e2e.py` —
  `agent_e2e_fixture_ready mode=seeded` after seeded session ready

### Log Structure

- Structured logs: yes (event prefix + `mode=` token)
- Includes context: yes (`mode=blank|seeded`)
- Log levels: INFO (ready)

## Metrics Implementation (if applicable)

N/A — no new metrics for this debt item.

## Monitoring Integration

Not applicable for this local pytest harness debt. Developers grep
`agent_e2e_fixture_ready` in CI/agent logs; catalog remains in
`doc/dev/logging.md`.

## Validation Results

Validation results:
- [x] Logs are correctly formatted (existing event prefixes)
- [x] Logging works in live ready scenarios
  (`test_live_agent_e2e_session_logs_fixture_ready_blank`,
  `test_live_seeded_agent_e2e_session_logs_fixture_ready_seeded`)
- [x] Large data structures are not logged

## Notes

Caplog proof (INFO path, not ERROR C1):
`caplog.at_level(logging.INFO, logger="tests._pytest_plugins.agent_e2e")`
plus `"agent_e2e_fixture_ready mode=blank|seeded" in caplog.text`.
Use `request.getfixturevalue` inside caplog block to capture fixture setup
logs. Complements PYPOST-867 mocked unit proofs.
