# PYPOST-1208: Observability Implementation

## Observability Requirements Analysis

- **Task nature:** ATTACH-3 verification / tests + docs alignment — not a
  new attach capability. Production attach IPC and sidecar logging already
  shipped under PYPOST-1207.
- **Key components under test:** `AgentUiAttachHost`, `AttachClientSession`,
  sidecar `--attach` path (subjects of `tests/test_agent_ui_attach.py`).
- **Critical paths exercised by verification:** bind/fail, host start/stop,
  catalog `ui_*` over attach, host-stop unbind, abrupt sidecar-exit rebind,
  endpoint override.
- **New instrumentation needed:** **N/A** — do not invent metrics or log
  events for a verification-only story. Rely on PYPOST-1207 events and the
  existing catalog in `doc/dev/logging.md`.

## Logging Implementation

### Added Logs

**None in this task.** Attach event catalog is unchanged from PYPOST-1207.

Existing coverage (reference only; see
[`ai-tasks/PYPOST-1207/50-observability.md`](../PYPOST-1207/50-observability.md)
and [`doc/dev/logging.md`](../../doc/dev/logging.md) § Agent-UI attach IPC):

- **EMERG / ALERT / CRIT / NOTICE**: N/A (same as PYPOST-1207)
- **ERR (ERROR)**: `agent_ui_attach_host_start_failed`,
  `agent_ui_attach_host_lifecycle action=start_failed`,
  `agent_ui_mcp_attach_failed`
- **WARNING**: `agent_ui_attach_bind_failed`, `agent_ui_attach_unknown_op`,
  `agent_ui_attach_ui_timeout`
- **INFO**: host started/stopped, client accepted/closed, handshake,
  detach, UI failed (type only), client bound/detached, `main` lifecycle,
  sidecar starting/ready/ended
- **DEBUG**: `agent_ui_attach_ui_dispatch` (`op`, `widget_id`,
  `in_current_tab`); shared `agent_ui_mcp_call_tool` on catalog path

### Log Structure

Log format used (unchanged):

- Structured logs: yes (`event_name key=value`)
- Includes context: yes (`endpoint`, `op`, `widget_id`, peer counts, error
  types)
- Log levels: ERROR, WARNING, INFO, DEBUG
- Large payloads: **not logged** — fill text, key modifiers, raw JSON bodies
  omitted
- Sidecar attach path logs to **stderr** (stdio remains MCP transport)

### Verification-related observability notes

- Automated proofs in `tests/test_agent_ui_attach.py` exercise the same
  production code paths that emit the catalog above; they are behavioral
  assertions (widget state, bind/unbind, endpoint resolution), not dedicated
  caplog contracts for every attach event.
- Failures in CI still surface via test assert messages; attach ERROR/WARNING
  events remain available when running under normal application logging.
- Manual residual gaps (protocol reject → PYPOST-1218; concurrent /
  stale-socket races) do **not** require new log events for this story —
  operators diagnosing those races can use existing accept/close /
  bind_failed / UI dispatch events.
- No new test-only loggers or fixture telemetry were added.

## Metrics Implementation (if applicable)

### Performance Metrics

- **Response time**: N/A — no new attach IPC histograms
- **Throughput**: N/A
- **Error rate**: N/A — failures remain visible via existing ERROR/WARNING/INFO

### Business Metrics

N/A — verification story; attach remains operator/agent assist, not a
product conversion funnel.

### System Health Metrics

N/A — host/client lifecycle still inferred from existing INFO events; no
Gauge series.

### Rationale (metrics N/A)

Same PYPOST-952 / PYPOST-1207 policy: attach AF_UNIX control plane is
logging-only. Expanding verification must not pull agent attach into
product `MetricsManager` / Prometheus without an explicit requirement.

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics — N/A (no new series; none required for ATTACH-3)
- [ ] Grafana dashboards — N/A
- [ ] Alerting rules — N/A
- [x] Structured application logs — already catalogued (PYPOST-1207)
- [x] CI / test gate — expanded `tests/test_agent_ui_attach.py` (ATTACH-3)

## Validation Results

Validation results:

- [x] No new instrumentation invented for this verification story
- [x] Existing attach events cross-checked against `doc/dev/logging.md` and
  PYPOST-1207 Step 6 artifact
- [x] Metrics remain N/A (documented; no false Prometheus claims)
- [x] Large data structures still not logged (policy unchanged)
- [x] Verification suite provides CI signal for attach paths that emit those
  logs in production runs

## Notes

- STEP 6 left at `[/]` in `00-roadmap.md` — executing agent does not mark
  `[x]`; acceptance-gate owner marks after review PASS.
- Full attach log catalog ownership remains PYPOST-1207; this artifact only
  records that ATTACH-3 adds no further observability surface.
- If a future defect in attach logging is found while running the expanded
  suite, fix under a capability/bug ticket — do not backfill speculative
  events here.
