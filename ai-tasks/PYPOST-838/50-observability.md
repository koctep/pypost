# PYPOST-838: Observability Implementation

## Logging Implementation

### Added Logs

This story is a **test-only composition proof** (`tests/test_agent_golden_e2e.py`).
No new production loggers or events were added. The golden run reuses sibling
agent DEBUG/INFO events and surfaces failure context on exceptions / pytest
assert messages (FR10), not via new syslog streams.

- **EMERG / ALERT / CRIT / ERR / NOTICE**: none added.
- **WARNING**: none added — ready-timeout WARNING remains on
  `AgentAppSession` (PYPOST-833) if launch never becomes ready.
- **INFO**: none added — lifecycle session start/ready/shutdown events from
  PYPOST-833 fire unchanged during the golden session.
- **DEBUG** (reused, not redefined):
  - `pypost.agent.lifecycle` — `agent_session_*` scalars (ports, timings).
  - `pypost.agent.ui_actions` — `ui_action_applied` (`primitive`, `widget_id`,
    `outcome`, `duration_ms`; never fill text / option labels).
  - `pypost.agent.ui_snapshot` — `ui_snapshot_captured` (`node_count`,
    `named_count`, `duration_ms`; never the tree).
  - `pypost.agent.ui_wait` — `ui_wait_settled` / `ui_wait_timeout`
    (`condition`, `waited_ms`, `timeout_s`; never tree / full text).

### Failure diagnostics (primary observability for this story)

Golden-specific diagnosability lives on the **exception / assert path**, not
in application logs:

| Failure | Diagnostic carrier |
| --- | --- |
| Wait timeout after Send | Rewrapped `UiWaitTimeoutError` with |
| | `step=wait_response_after_send` and clipped `response_excerpt` |
| | (RESPONSE_PANEL values, ≤400 chars) plus sibling wait diagnostics |
| Wrong status/body | pytest assert message includes expected value + |
| | `_response_panel_excerpt` |
| Missing control | `UiTargetNotFoundError` / interactable errors from actions |
| Ready never happens | Existing lifecycle timeout / `agent_session_ready_timeout` |

No full snapshot trees or pretty-printed response bodies are dumped on success.
Excerpts are clipped and panel-scoped.

### Log Structure

Log format used:
- Structured logs: yes (`event_name key=value` per `doc/dev/logging.md`) —
  sibling agent modules only
- Includes context: yes (widget_id / timing scalars on DEBUG; step + excerpt on
  wait-timeout exception)
- Log levels: INFO / WARNING / DEBUG from siblings; no new levels from this
  story

Diagnostics for golden correctness:

- Exception path: `UiWaitTimeoutError.diagnostics` enriched in
  `tests/test_agent_golden_e2e.py`
- Assert path: `_assert_response_ui` messages with panel excerpt
- Automated: `tests/test_agent_golden_e2e.py`
- Manual: `make test PYTEST_ARGS="tests/test_agent_golden_e2e.py -v"`;
  enable DEBUG to see sibling `ui_*` / `agent_session_*` events

## Metrics Implementation (if applicable)

### Performance Metrics

No Prometheus / OTel instruments. Wait duration remains sibling DEBUG
`waited_ms`. Agent sessions keep ephemeral metrics ports (PYPOST-833); the
golden test does not scrape or assert metrics.

### Business Metrics

None.

### System Health Metrics

None new.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics — not applicable for ephemeral agent / pytest runs
- [ ] Grafana dashboards — not applicable
- [ ] Alerting rules — not applicable
- [x] CI / test gate — `tests/test_agent_golden_e2e.py` under `make test`
  (offscreen)
- [x] Log aggregation — reused sibling DEBUG/INFO events follow
  `event_name key=value`

## Validation Results

Validation results:
- [x] Logs are correctly formatted — no new events; siblings already validated
- [x] Metrics are collected correctly — N/A (no new metrics)
- [x] Logging works in error scenarios — wait timeout rewrap + assert excerpts
- [x] Large data structures are not logged — no tree dumps; excerpt ≤400 chars
- [x] Metrics are available for monitoring — N/A

## Notes

Same posture as PYPOST-837: DEBUG scalars from the agent stack, actionable
exceptions for callers, CI as the primary gate. Heavy production metrics would
be inventing signal for a composition test — deferred / out of scope.
Run-path and failure table: `doc/dev/agent_golden_e2e.md`.
