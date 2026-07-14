# PYPOST-799: Observability Implementation

Verification-only closure for PYPOST-44 TD-2 — no new logs or metrics were added. Step 5
confirms the existing `NullMetrics` observability pattern preserves production telemetry when
metrics is configured and silent omission when it is not.

## Logging Implementation

### Added Logs

No new logs added in this task. Optional-metrics guard removal does not change logging
behavior:

- **EMERG**: N/A — no changes
- **ALERT**: N/A — no changes
- **CRIT**: N/A — no changes
- **ERR**: N/A — no changes
- **WARNING**: N/A — no changes
- **NOTICE**: N/A — no changes
- **INFO**: N/A — no changes
- **DEBUG**: N/A — no changes

`NullMetrics` is intentionally silent — it absorbs tracking calls without emitting log lines
or registry side effects. Domain and error logging at consumer call sites is unchanged.

### Log Structure

Log format used:

- Structured logs: unchanged (existing application logging)
- Includes context: unchanged
- Log levels: unchanged — no new levels introduced by this closure

## Metrics Implementation

### NullMetrics observability pattern

| Scenario | Behavior | Verified |
| --- | --- | --- |
| Metrics omitted at composition root | `resolve_metrics(None)` → shared `NULL_METRICS`; all `track_*` / `set_mcp_server_up` calls are no-ops with zero Prometheus registry side effects | Yes |
| Metrics injected (`MetricsManager`, `OtelMetricsTracker`) | Counters, gauges, and events flow through unchanged — same metric names, labels, and semantics as pre-closure | Yes |
| Direct recording at consumers | 11 `resolve_metrics` normalization sites; zero `if self._metrics` optional-injection guards in `pypost/` | Yes |

### Performance Metrics

No new performance metrics added. Existing metrics unchanged:

- **Response time**: `track_mcp_tool_call_duration`, `track_template_expression_render_duration` — unchanged call sites
- **Throughput**: request/MCP/history counters — unchanged semantics
- **Error rate**: `track_request_error`, encryption error counters — unchanged semantics

### Business Metrics

Business metrics preserved — consumers call `self._metrics.track_*()` unconditionally:

- GUI actions (send, save, collection ops, search) — `RequestEditor`, `TabsPresenter`, etc.
- HTTP/MCP request lifecycle — `RequestService`, `HTTPClient`, `MCPServerImpl`
- History, templates, environments — `StorageManager`, `TemplateService`, `EnvironmentVariablesAdapter`

When metrics is omitted, these calls reach `NullMetrics` and produce no observability output.

### System Health Metrics

System health metrics unchanged:

- **MCP server status**: `set_mcp_server_up` — no-op via `NullMetrics` when omitted; real gauge when configured
- **Component status**: Prometheus exposition via `MetricsManager` at composition root — unchanged

## Monitoring Integration

Integration with monitoring systems (unchanged from pre-closure):

- [x] Prometheus metrics — `MetricsManager` when injected at `main.py`
- [ ] Grafana dashboards — out of scope (deployment concern)
- [ ] Alerting rules — out of scope (deployment concern)
- [ ] Log aggregation (ELK, Loki, etc.) — out of scope (deployment concern)

## Validation Results

Validation results:

- [x] Logs are correctly formatted — no log changes in this task; existing format unchanged
- [x] Metrics are collected correctly — `MetricsManager` still satisfies `MetricsTrackerProtocol`; injected trackers receive all `track_*` calls
- [x] Logging works in error scenarios — domain error logging unchanged; `NullMetrics.track_request_error` is a no-op when omitted
- [x] Large data structures are not logged — no new logging added
- [x] Metrics are available for monitoring — when `MetricsManager` is injected, Prometheus counters behave as before; when omitted, silent no-op path confirmed

### Test evidence

- `tests/test_metrics_protocol.py` — `NullMetrics` / `NULL_METRICS` satisfy protocol; no-op smoke; `resolve_metrics(None)` returns shared singleton; injected mock forwarded unchanged
- `make test` — **1587 passed**, 1 deselected, 61 subtests (~71s) — full suite green after Step 3/4 verification

### Call-site clarity

Observability calls remain inline with business logic (no optional-injection guards):

```python
self._metrics.track_request_sent(request.method)
response = self.mcp_client.run(url, operation, call_params)
self._metrics.track_response_received(request.method, str(response.status_code))
```

Domain-specific suppression (e.g. skip error metric on user cancellation) remains explicit and
is not optional-injection plumbing.

## Notes

- **Verification-only task** — PYPOST-73/74 delivered `NullMetrics`, `NULL_METRICS`, and
  `resolve_metrics()`; Step 5 confirms observability semantics are production-ready without
  code changes.
- **Silent omission is by design** — omitted metrics must not surface errors or alter product
  workflows; `NullMetrics` preserves the pre-guard "skip tracking" behavior without branching.
- **No regression when configured** — Prometheus metric names, labels, and counter semantics
  unchanged; tracking calls that previously ran only when metrics was injected still run through
  the same protocol surface, now via direct calls instead of guarded calls.
- Follow-up observability work (OpenTelemetry adapter, type-hint narrowing) tracked separately —
  [PYPOST-579](https://pypost.atlassian.net/browse/PYPOST-579), [PYPOST-675](https://pypost.atlassian.net/browse/PYPOST-675).
