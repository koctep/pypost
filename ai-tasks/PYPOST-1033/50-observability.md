# PYPOST-1033: Observability Implementation

## Verdict

**No new logging or metrics.** This bug fix only widens
`FunctionExpressionResolver._SAFE_PATH_RE` so safe dotted paths
(e.g. `mcp.request.issue_key`) validate. The resolver stays log-free by
design; render-path observability already lives in `TemplateService` /
`template_service_render.py` and adequately covers both the new happy path
and remaining fail-closed cases.

## Observability Requirements Analysis

| Area | Finding |
| ---- | ------- |
| Key components | `FunctionExpressionResolver` (grammar gate), `TemplateService` (validate → Jinja → fallback), MCP `call_tool` merge (unchanged) |
| Critical paths | Validation accept/reject for dotted paths; render success; fail-closed fallback on `invalid_syntax` / other errors |
| Performance metrics | Existing template render attempt / duration / validation-failure counters suffice; no new hot path |

After the fix, safe `mcp.request.*` expressions take the success path instead of
the prior false `invalid_syntax` → fallback sequence. Unsafe forms
(`db.__class__`, `mcp.request.__class__`, filters) still fail closed with the
same validation and fallback signals.

## Logging Implementation

### Added Logs

None. No production logging was added in this step.

- **EMERG / ALERT / CRIT / ERR / NOTICE**: N/A
- **WARNING / INFO / DEBUG**: N/A (new); existing TemplateService logs retained

### Existing Logs (adequate; unchanged)

| Level | Location | Event | Relevance to PYPOST-1033 |
| ----- | -------- | ----- | ------------------------ |
| INFO | `template_service_render.emit_validation_failure_observability` | `template_expression_validation_failed` (`render_path`, `code`, `function_name`, `token_count`) | Still emitted when validation fails (e.g. `code=invalid_syntax` for underscore attribute segments). Safe MCP paths no longer hit this falsely. |
| WARNING | `template_service_render.fallback_content_after_render_exception` | `template_render_fallback_to_original` (`render_path`, `error_type`, `token_count`) | Fail-closed return of original content; includes validation `ValueError` and Jinja errors. Does not log template body or variable values. |
| DEBUG | `template_service_render.emit_render_success_observability` | `template_expression_render_succeeded` (`render_path`, `token_count`) | Now reached for successful `mcp.request.*` renders. |
| DEBUG | `mcp_server_impl` (PYPOST-550) | `mcp_execution_variables_merged` (`env_var_count`, `mcp_arg_count`) | Confirms MCP args entered the merge; counts only, no values. |

`FunctionExpressionResolver` remains without a logger (same as PYPOST-461):
validation outcomes surface only when `TemplateService.render_string` runs.

### Log Structure

- Structured logs: **yes** — fixed message prefixes with keyed fields
- Includes context: **yes** — `render_path`, `code`, `function_name`,
  `token_count`, `error_type`; no template content or secret values
- Log levels used on this path: **INFO**, **WARNING**, **DEBUG**

## Metrics Implementation (if applicable)

### Performance Metrics

No new metrics. Existing instruments apply:

- **Render attempts**: `track_template_expression_render_attempt`
  (`outcome`: `success` / `validation_error` / `render_error` / `empty_content`)
- **Duration**: `track_template_expression_render_duration` (`render_path`)
- **Error / validation rate**:
  `template_expression_validation_failures_total{render_path,code,function_name}`
  (includes `code=invalid_syntax`)

Effect of this change: legitimate `mcp.request.*` traffic shifts from
`validation_error` + fallback toward `success`. Unsafe forms continue to
increment `invalid_syntax` validation failures.

### Business Metrics

None added. MCP call volume remains on existing MCP request/response counters
(unchanged by this grammar fix).

### System Health Metrics

None added.

## Monitoring Integration

Integration with monitoring systems:

- [x] Prometheus metrics — reuse existing template expression series
  (`doc/prometheus_monitoring.md`)
- [ ] Grafana dashboards — no new panels required
- [ ] Alerting rules — no new rules; false `invalid_syntax` noise for safe
  dotted MCP paths should decrease
- [ ] Log aggregation (ELK, Loki, etc.) — N/A for this change

## Validation Results

Validation results:

- [x] No new application logs required — existing TemplateService coverage
  adequate for the grammar widen
- [x] No new metrics invented
- [x] Validation-failure INFO + fallback WARNING still cover reject path
  (unsafe dotted forms locked by tests)
- [x] Large data structures / secrets are not logged (counts and codes only)
- [x] Metrics available via existing Prometheus template expression instruments
- [x] Resolver stays log-free; orchestration observability unchanged

## Notes

Adding per-accept DEBUG logs inside `FunctionExpressionResolver` for every
safe path would duplicate success signals already emitted by
`emit_render_success_observability` and would spam high-volume render paths.
Per-reject logging in the resolver would similarly duplicate
`template_expression_validation_failed`. Prefer documenting the existing
orchestration hooks over new resolver instrumentation.

References:

- `pypost/core/template_service_render.py` — validation / success / fallback
  observability
- `doc/dev/logging.md` — `template_expression_validation_failed`,
  `template_render_fallback_to_original`
- `doc/prometheus_monitoring.md` —
  `template_expression_validation_failures_total`
- Prior art: `ai-tasks/PYPOST-461/50-observability.md` (resolver log-free)
