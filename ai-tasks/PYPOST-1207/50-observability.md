# PYPOST-1207: Observability Implementation

## Observability Requirements Analysis

- **Key components:** `AgentUiAttachHost`, `AttachClientSession`, sidecar
  `--attach` path, interactive `main()` composition root.
- **Critical paths:** Host start/stop; client bind / unbound fail;
  handshake; detach; per-peer accept/close; GUI-thread `ui_*` dispatch.
- **Performance / health metrics:** Logging-only for attach IPC
  (PYPOST-952 agent-UI MCP policy); no new Prometheus series.

## Logging Implementation

### Added Logs

- **EMERG**: N/A — attach IPC is cooperative local tooling, not a crash domain
- **ALERT**: N/A
- **CRIT**: N/A
- **ERR** (`ERROR`):
  - `pypost.agent.attach_ipc` — `agent_ui_attach_host_start_failed`
    (`endpoint`, `error` type) when AF_UNIX bind/listen fails
  - `pypost.main` — `agent_ui_attach_host_lifecycle action=start_failed`
    (`endpoint`, `error` type) when composition-root host start fails
  - `pypost.agent.ui_actions_mcp` — `agent_ui_mcp_attach_failed`
    (`endpoint`, `error` type) when `--attach` cannot bind (unbound host)
- **WARNING**:
  - `AttachClientSession.connect` — `agent_ui_attach_bind_failed`
    (`endpoint`, `reason`=`connect`/`handshake`/`rejected`, `error` type)
  - Host — `agent_ui_attach_unknown_op` (`endpoint`, `op`)
  - Host — `agent_ui_attach_ui_timeout` (`op`, `widget_id`)
- **NOTICE**: N/A (Python logging has no NOTICE; significant events use INFO)
- **INFO**:
  - Host — `agent_ui_attach_host_started` / `agent_ui_attach_host_stopped`
    (`endpoint`)
  - Host — `agent_ui_attach_client_accepted` / `agent_ui_attach_client_closed`
    (`endpoint`, `peers`)
  - Host — `agent_ui_attach_handshake_ok` (`endpoint`, `version`)
  - Host — `agent_ui_attach_detach_received` (`endpoint`)
  - Host — `agent_ui_attach_ui_failed` (`op`, `widget_id`, `error` type)
  - Client — `agent_ui_attach_bound` / `agent_ui_attach_detached` (`endpoint`)
  - `main` — `agent_ui_attach_host_lifecycle action=start|stop` (`endpoint`)
  - Sidecar — `agent_ui_mcp_attach_starting` / `agent_ui_mcp_attach_ready` /
    `agent_ui_mcp_attach_ended` (`endpoint`)
- **DEBUG**:
  - Host — `agent_ui_attach_ui_dispatch` (`op`, `widget_id`, `in_current_tab`)
  - Existing sidecar — `agent_ui_mcp_call_tool` (unchanged; shared catalog path)

### Log Structure

Log format used:

- Structured logs: yes (`event_name key=value` message text)
- Includes context: yes (`endpoint`, `op`, `widget_id`, peer counts, error types)
- Log levels: ERROR, WARNING, INFO, DEBUG
- Large payloads: **not logged** — fill `text`, key modifiers payloads, and
  raw JSON request bodies are omitted (widget id / op only)
- Sidecar attach path logs to **stderr** (stdio remains MCP transport)

## Metrics Implementation (if applicable)

### Performance Metrics

- **Response time**: N/A — no attach IPC Prometheus histogram
- **Throughput**: N/A — no attach request counters
- **Error rate**: N/A — failures visible via ERROR/WARNING/INFO logs

### Business Metrics

N/A — attach is an operator/agent assist path, not a product request conversion.

### System Health Metrics

- **Resource usage**: N/A for attach IPC
- **Component status**: inferred from host start/stop and client accept/close
  INFO events (no Gauge series)

### Rationale (metrics N/A)

Matches PYPOST-952 agent-UI MCP policy: the attach sidecar and AF_UNIX
control plane do not integrate with product `MetricsManager` / Prometheus.
Wiring counters through `MetricsRegistry` + OTel + protocol would expand the
agent package into the product metrics surface without an ATTACH-1
requirement. Desktop `MetricsManager` remains for product HTTP/MCP/GUI only.

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics — N/A for attach IPC v1 (no new series)
- [ ] Grafana dashboards — N/A
- [ ] Alerting rules — N/A
- [x] Structured application logs (host + sidecar stderr + `main`)
- [x] CI / test gate — `tests/test_agent_ui_attach.py`

## Validation Results

Validation results:

- [x] Logs use `event_name key=value` format consistent with agent modules
- [x] Metrics N/A documented (no false Prometheus claims)
- [x] Unbound attach and host start failures emit ERROR/WARNING with types
- [x] Fill text and request bodies are not logged
- [x] Lifecycle coverage: start/stop, bind/fail, handshake, accept/close,
  detach, UI dispatch/fail/timeout
- [x] Attach tests exercised after logging changes

## Notes

- STEP 6 left at `[/]` in `00-roadmap.md` — executing agent does not mark
  `[x]`; acceptance-gate owner marks after review PASS.
- Host-side UI failure logs exception **type** only (message stays in IPC
  reply to the sidecar, not duplicated into host logs).
- Full attach verification matrix remains PYPOST-1208 (ATTACH-3).
