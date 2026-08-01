# PYPOST-918: Observability Implementation

## Logging Implementation

### Added Logs

**N/A — no new runtime logs.** This debt is docs-only packaging clarity
(Option A path in `doc/dev/ui_actions.md` + MCP cross-links) and a
doc-token contract lock
(`tests/test_ui_actions_mcp_packaging_doc.py`). No out-of-process MCP
bridge, no production Python changes, and no new syslog events.

- **EMERG**: N/A
- **ALERT**: N/A
- **CRIT**: N/A
- **ERR**: N/A
- **WARNING**: N/A
- **NOTICE**: N/A
- **INFO**: N/A
- **DEBUG**: N/A (new) — existing in-process `ui_action_applied` DEBUG
  events in `pypost.agent.ui_actions` are **unchanged** by this ticket
  (click / fill / select / send_key scalars; fill text never logged).
  Catalog / docs: `doc/dev/ui_actions.md`, `doc/dev/logging.md`.

### Log Structure

Log format used:
- Structured logs: N/A for this debt (no new events). Sibling in-process
  actions continue `event_name key=value` per `doc/dev/logging.md`.
- Includes context: N/A (new). Existing `ui_action_applied` keeps
  `primitive`, `widget_id`, `outcome`, `duration_ms` (and fill-only
  `via_key_clicks` when applicable).
- Log levels: N/A (new). Unchanged DEBUG from `pypost.agent.ui_actions`.

Failure / drift mode for this story is **pytest doc-token assert**, not
application logging. Contract lock timeouts:
`pytestmark = pytest.mark.timeout(10)` on
`tests/test_ui_actions_mcp_packaging_doc.py`.

## Metrics Implementation (if applicable)

### Performance Metrics

**N/A — no new metrics.** No bridge process, no MCP packaging runner, and
no production path to instrument. In-process `duration_ms` on
`ui_action_applied` remains as shipped by prior UI-action work
(PYPOST-851 / siblings); this debt does not extend or scrape it.

- **Response time**: N/A
- **Throughput**: N/A
- **Error rate**: N/A

### Business Metrics

Business metrics:
- N/A

### System Health Metrics

System health metrics:
- **Resource usage**: N/A
- **Component status**: N/A — product `MCPServerImpl` and in-process
  `ui_actions` runtime behaviour are intentionally unchanged.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics — not applicable (docs / contract debt)
- [ ] Grafana dashboards — not applicable
- [ ] Alerting rules — not applicable
- [ ] Log aggregation (ELK, Loki, etc.) — not applicable for new events
- [x] CI / test gate — `tests/test_ui_actions_mcp_packaging_doc.py`
  under `make test` (doc-token lock; no Qt / live MCP)
- [x] Discoverability (not runtime monitoring) —
  `doc/dev/ui_actions.md` packaging path + cross-links from
  `mcp_integration.md`, `mcp_trust_model.md`, `agent_lifecycle.md`

## Validation Results

Validation results:
- [x] No new application logs required for DoD
- [x] No metrics required for DoD
- [x] Existing `ui_action_applied` logging left unchanged (no bridge to
  log against)
- [x] Large data structures are not logged (N/A — no new log sites)
- [x] Failure mode for packaging-doc drift is pytest lock, not runtime
  logging
- [x] Metrics available for monitoring — N/A

## Notes

Observability for PYPOST-918 is the **automated wording lock** and
discoverable packaging documentation, not syslog or Prometheus.

Architecture (`20-architecture.md`) already marked Steps 5–7 as
likely N/A or pointer-only for observability: documented packaging path
only; live agent-UI MCP entry is future work and would own its own
bind/trust and logging when prioritized (record only in
`60-tech-debt.md` if needed).

Same posture as sibling docs-packaging debt PYPOST-922: no runtime
application path changed; contract tests + `doc/dev/` are the gate.

Roadmap STEP 6 left `[/]` pending Step 6 review (orchestrator).
