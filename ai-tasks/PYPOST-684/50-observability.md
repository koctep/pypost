# PYPOST-684: Observability Implementation

**Task type:** Audit only — no application code changes.

## Logging Implementation

### Added Logs

None. This step documents existing observability posture and audit findings only.

### Log Structure

N/A — no new instrumentation.

## Metrics Implementation

### Performance Metrics

N/A — no new metrics added.

### Business Metrics

N/A — no new metrics added.

### System Health Metrics

N/A — no new metrics added.

## Monitoring Integration

Production instrumentation: **N/A** for this task.

Existing integration (unchanged; observed during audit):

- `MetricsManager` wired in `main.py` composition root
- `MetricsServer` exposes observability MCP resources (`metrics://all`) — separate from collection MCP (`S-MCP-003`)
- `MetricsTrackerProtocol` seam used by `RequestService` and tests (`D-006`)

## Validation Results

- [x] Audit confirms no logging or metrics changes required for boundary audit scope
- [x] Existing observability surfaces documented for reference
- [ ] Production instrumentation added (not applicable — audit only)

## Audit Findings (from `30-audit-report.md`)

Observability-related items summarized for Step 6 / dev-docs follow-up:

| ID | Severity | Finding | Impact |
| --- | --- | --- | --- |
| S-MCP-003 | PASS | `MetricsServer` is a distinct MCP surface for `metrics://all`; shares transport helpers with collection MCP but separate server instance | Observability MCP boundary is clear; no blur with inbound collection tools |
| S-MCP-005 | PASS | `McpActivityLog` owned by `MCPServerManager`; UI reads via signals | Activity logging ownership is centralized in core lifecycle manager |
| S-TMPL-003 | MEDIUM | Module-level `_hover_template_service` in `ui/widgets/mixins.py` is separate from composition-root `TemplateService`; metrics diverge unless `VariableHoverResolver.set_metrics()` is wired (done from `MainWindow`) | Template render metrics may under-count hover path if wiring regresses |
| S-HIST-004 | LOW (documented) | Inbound MCP `call_tool` omits `history_manager` on per-call `RequestService` | GUI executions get history/audit trail; inbound MCP does not — asymmetric by design per `mcp_integration.md` |
| D-004 | MEDIUM | `core/metrics.py` depends on PySide6 (`QObject`, `Signal`) | Metrics collection tied to Qt event loop; same core/Qt coupling pattern as workers and MCP manager |
| Doc gap | MEDIUM | `architecture.md` tree omits `metrics_server` and related modules among ~40 missing core entries (`R-P2-005`) | Observability stack under-documented in primary architecture doc |

**Composition root (observability-relevant):** `main.py` wires `MetricsManager` and `AlertManager` alongside `ConfigManager` and `TemplateService`. `HistoryManager` and MCP lifecycle remain constructed in `MainWindow` (`S-HIST-003`), which affects where execution-history observability is wired vs. metrics at startup.

**Out of scope per audit:** Performance profiling and security penetration testing were not performed (`30-audit-report.md` § Out of Scope).

## Notes

- Step 5 is verification-only for PYPOST-684; remediation of boundary or documentation gaps belongs in Steps 6–7.
- No structured logging, counters, or dashboards were added; existing `RequestService`, MCP, and metrics-server instrumentation was inventoried during the audit and left unchanged.
