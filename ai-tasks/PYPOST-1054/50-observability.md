# PYPOST-1054: Observability Implementation

## Logging Implementation

### Added Logs

- **INFO**: `pypost/core/mcp_server_impl.py::MCPServerImpl._build_execution_variables` —
  new `mcp_param_default_applied method=%s param=%s default=%r` line, emitted once per
  optional MCP tool parameter that gets silently filled from its declared `default`
  because the caller (agent) omitted it or passed `None`. This is the "significant event
  notification" (syslog NOTICE-equivalent; the project maps NOTICE to Python's `INFO`, the
  same mapping already used for `mcp_activity_recorded` in `mcp_activity_log.py`) that makes
  the new default-application code path visible in production logs — previously a caller
  omitting `maxResults`/`startAt` produced no distinguishable signal in the logs at all.
  `param` is the declared MCP param name (e.g. `maxResults`) and `default` is the static
  config-declared fallback value (e.g. `50`) — both come from the curated tool contract
  (`request_data.mcp_params`), already published to agents via `list_tools`'s JSON schema
  (Step 4's `build_tool_input_schema` change), so neither is sensitive or a "large data
  structure."
- **DEBUG** (extended, pre-existing line): `mcp_execution_variables_merged` in the same
  function gained a new `defaults_applied_count=%d` field so the existing aggregate,
  counts-only diagnostic line (env var / hidden key / mcp arg counts) also reports how many
  params were defaulted on this call, without repeating names/values already covered by the
  new INFO line above.
- **EMERG / ALERT / CRIT**: not applicable — default-application is expected, successful
  behavior, never a system failure.
- **ERR / WARNING**: not applicable — applying a declared default is not an error or a
  degraded-service condition (contrast with the existing `response_body_truncated` WARNING
  in `http_client.py`, which flags data loss; nothing is lost here, a documented fallback is
  used).

### Log Structure

- Structured logs: yes — `key=value` tokens, matching every other log line in
  `mcp_server_impl.py` (`mcp_execution_variables_merged`, `mcp_activity_recorded`, etc.).
- Includes context: yes — HTTP `method`, the defaulted `param` name, and the `default` value
  actually substituted (all non-secret, config-declared values).
- Log levels used: `INFO` (new event line) and `DEBUG` (extended aggregate line, pre-existing).

## Metrics Implementation

### Convention Followed

`pypost/core/mcp_server_impl.py` and `pypost/core/http_client.py` already establish the
project's convention for "the system silently modified caller-facing behavior on the
caller's behalf": pair a counter metric with a log line at the exact point the behavior
occurs. The precedent is `track_response_body_truncated(method)` +
`logger.warning("response_body_truncated ...")` in `http_client.py` for response truncation.
This task's default-application path is structurally the same kind of event (an omitted
input silently gets a substitute value), so it follows the identical pattern: one counter,
incremented at the point of substitution, alongside the new log line above.

Cardinality note: existing MCP metrics (`mcp_requests_received_total`,
`mcp_responses_sent_total`, `mcp_tool_call_duration_seconds`) are deliberately labeled only
by the coarse, bounded HTTP `method` (GET/POST/…), never by user-defined tool or parameter
names, to avoid unbounded Prometheus label cardinality from arbitrary user-created MCP tools.
The new metric follows the same bound: `mcp_param_defaults_applied_total{method=...}` —
no `param` label, even though the specific defaulted param names are logged (logs tolerate
higher-cardinality context; Prometheus labels do not).

### Performance Metrics

- No new latency/throughput metrics added — default substitution is a synchronous, in-memory
  dict lookup with no I/O; it's already inside the span covered by the existing
  `mcp_tool_call_duration_seconds` histogram (`track_mcp_tool_call_duration`, unchanged).

### Business Metrics

- **`mcp_param_defaults_applied_total{method}`** (new Counter): number of optional MCP tool
  parameters filled from their declared default because the caller omitted them. Location:
  incremented in `MCPServerImpl._build_execution_variables`
  (`pypost/core/mcp_server_impl.py`), once per parameter defaulted. Answers the ergonomics
  question this task exists to address — how often agents actually rely on the new pagination
  defaults vs. supplying explicit `maxResults`/`startAt` — and gives an operator a real signal
  for the "should more list tools get defaults" follow-up decision. Threaded through all four
  places every other `MetricsTrackerProtocol` metric lives:
  - `pypost/core/metrics_protocol.py` — protocol method + `NullMetrics` no-op
  - `pypost/core/metrics_registry.py` — Prometheus `Counter`
    (`mcp_param_defaults_applied_total`, label `method`)
  - `pypost/core/metrics_otel.py` — mirrored OTel counter instrument
  - `pypost/core/qt/metrics.py` — `MetricsManager` facade delegation

### System Health Metrics

- Not applicable — this code path has no resource/component-status dimension; it's a pure
  per-call data-defaulting decision inside an already-instrumented request lifecycle.

## Monitoring Integration

- [x] Prometheus metrics — `mcp_param_defaults_applied_total{method}` exported via the
  existing `MetricsRegistry` / `/metrics` endpoint (same wiring as every other counter in the
  registry; no new endpoint or scrape config needed).
- [x] OpenTelemetry metrics — mirrored in `OtelMetricsTracker` for deployments that swap the
  Prometheus tracker for OTel export (existing swap mechanism, unchanged).
- [ ] Grafana dashboards — none added; out of scope for this task (no existing MCP-specific
  dashboard exists in-repo to extend, per Steps 1-5's requirements/architecture scope).
- [ ] Alerting rules — none added; this metric is diagnostic/ergonomics telemetry, not a
  failure signal, so no alert threshold applies.
- [x] Log aggregation — the new INFO line uses the same structured `key=value` format and
  logger namespace (`pypost.core.mcp_server_impl`) already ingested by whatever log
  aggregation the deployment uses for the rest of this module; no new sink required.

## Validation Results

- [x] Logs are correctly formatted — verified via
  `tests/test_mcp_server_impl.py::TestMCPServerImpl::test_call_tool_applying_defaults_tracks_metric_and_logs`,
  which asserts on `self.assertLogs("pypost.core.mcp_server_impl", level=logging.INFO)` that
  exactly one `mcp_param_default_applied` line is emitted per defaulted param, with the
  correct `param=` name for both `maxResults` and `startAt`.
- [x] Metrics are collected correctly — same test asserts
  `mock_metrics.track_mcp_param_default_applied` is called once per defaulted param (twice
  total) with the correct HTTP `method` argument (`"GET"`); `tests/test_metrics_registry.py`,
  `tests/test_metrics_otel.py`, and `tests/test_metrics_manager.py` each add a unit test
  confirming the counter increments and scrapes/exports with the expected `method` label
  through the Prometheus registry, the OTel tracker, and the Qt facade respectively.
- [x] Logging works in error/negative scenarios — added
  `test_call_tool_explicit_args_skip_default_metric_and_logs`, which supplies explicit
  `maxResults`/`startAt` and asserts the metric is *not* called, no
  `mcp_param_default_applied` line appears, and the extended DEBUG aggregate line reports
  `defaults_applied_count=0` — confirming the new observability path stays silent when there
  is nothing to report.
- [x] Large data structures are not logged — only the defaulted param name (schema field
  identifier, already public via `list_tools`) and its small scalar default value (already
  published in the JSON schema `default:` property since Step 4) are logged; no request
  bodies, headers, env vars, or hidden secrets are touched by this change.
- [x] Metrics are available for monitoring — counter is registered in the same
  `CollectorRegistry` (`MetricsRegistry`) served by the existing `/metrics` HTTP endpoint and
  MCP `metrics://` resource (`MetricsServer`), so it is scraped/read exactly like every other
  MCP counter without additional wiring.

## Notes

- No new logging/metrics conventions were invented — this step exclusively reuses two
  patterns already established in the codebase: (1) `McpSecretsPolicy.safe_execution_log_fields`'s
  "counts only, no names/values for potentially-sensitive fields" convention for the
  pre-existing aggregate DEBUG line (extended, not replaced), and (2)
  `track_response_body_truncated` + `logger.warning`'s "counter + log line at the point of
  silent behavior substitution" convention (mirrored at INFO instead of WARNING, since
  applying a documented default is expected/successful behavior, not a degraded-service
  condition).
- Adding the new `MetricsTrackerProtocol` method touched four files
  (`metrics_protocol.py`, `metrics_registry.py`, `metrics_otel.py`, `qt/metrics.py`) — this is
  the codebase's existing fan-out for *every* tracked metric (confirmed by grepping
  `track_mcp_active_env_changed` across the same four files), not scope creep specific to
  this task.
- `pypost/core/qt/metrics.py` grew from 179 to 182 lines, which exceeded its
  `ai-tasks/PYPOST-376/baseline-metrics.md` SOLID-audit cap of 181 (`FILE_CAPS` in
  `scripts/audit_baseline_metrics.py`) by one line. Re-derived the cap to 185 with an inline
  `# PYPOST-1054:` justification comment (matching the file's existing precedent of
  documented cap re-derivations, e.g. the `PYPOST-1071` entries) and regenerated
  `ai-tasks/PYPOST-376/baseline-metrics.md` via the script's documented command. Re-ran
  `tests/test_solid_audit_baseline.py`: 4/4 pass. `pypost/core/mcp_server_impl.py` also grew
  (293 → 303 lines per Step 5's already-regenerated baseline) but remains well inside its
  325-line cap, no re-derivation needed there.
- Ran `make lint` (clean on `pypost/`), explicit `flake8 --select=F401,E501,F841` against all
  touched test files (clean), `make typecheck` (227 baseline-drift errors, confirmed via
  `git stash` to be byte-for-byte identical to unmodified `dev` and unrelated to any file this
  step touched — same pre-existing drift Step 5 already flagged), `make check-mcp-fixtures`
  (up to date), and `make verify-ai-tasks` (baseline OK).
- Full targeted re-run: `pytest tests/test_mcp_server_impl.py tests/test_mcp_tool_contract.py
  tests/test_example_fixtures.py tests/test_request_editor_mcp_params.py
  tests/test_solid_audit_baseline.py tests/test_metrics_registry.py tests/test_metrics_otel.py
  tests/test_metrics_manager.py tests/test_metrics_protocol.py` — 144 passed.
