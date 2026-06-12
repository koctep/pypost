# PYPOST-685: Observability Implementation

**Task type:** Audit only — no application code changes.

## Logging Implementation

### Added Logs

None. This step documents existing logging posture and security-related audit findings only.

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

- `MetricsManager` and `MetricsServer` expose Prometheus scrape and metrics MCP resources
- `RequestService` emits history-entry observability at DEBUG after masking is applied
- `McpActivityLog` records MCP invocations with argument counts only (no values)
- `AlertManager` and optional `pypost-alerts.log` for retry-exhaustion webhooks

## Validation Results

- [x] Audit confirms no logging or metrics changes required for security audit scope
- [x] Security-relevant logging and metrics surfaces documented for reference
- [ ] Production instrumentation added (not applicable — audit only)

## Audit Findings (from `30-audit-report.md`)

Security-related logging, metrics, and observability surfaces summarized for Step 6 / dev-docs
follow-up:

### Logging — credential and URL exposure

| ID | Severity | Finding | Impact |
| --- | --- | --- | --- |
| E-003 | P2 | `HTTPClient.send_request` logs fully resolved `url` at **ERROR** on timeout, connection failure, or request exception | Support log bundles and shared debug output may contain live credentials from URL templates or query tokens |
| E-004 | PASS (caveat) | `RequestService._emit_history_entry_observability` logs masked URL at DEBUG after `SensitiveDataMaskingPolicy` runs | Safe when `hidden_keys` is non-empty; fully resolved URL logged when masking scope is empty (same as E-001) |
| E-005 | PASS | Retry-exhaustion warnings, `AlertPayload.endpoint`, and `track_request_retry_exhaustion` use template `request.url`, not resolved fields | Reduces secret leakage in alerts and Prometheus `endpoint` labels |
| E-006 | PASS | `HiddenToggleLogPolicy.format_key_name` redacts hidden key names unless `AppSettings.log_hidden_key_names` is true | Env-dialog toggle logs align with operator privacy preference |
| S-001 | PASS | Encryption error paths log env name and variable key name only (`environment_value_encrypt_failed`), not values | At-rest failure diagnostics do not emit decrypted or plaintext secrets |

### Logging — MCP and agent-visible output

| ID | Severity | Finding | Impact |
| --- | --- | --- | --- |
| M-003 | P2 | Post-script `result.script_logs` included in MCP tool result JSON under `logs` | Operator scripts can `pypost.log()` env values or response fragments back to external agents |
| M-004 | PASS | `McpActivityEntry` stores `mcp_arg_count` only; no argument keys or values in activity log | Matches `mcp_integration.md`; MCP activity table is count-only |
| M-002 | P1 | `format_structured_tool_result` serializes full upstream `result.response.body` into MCP JSON text | Highest-risk agent-visible leakage path; distinct from application logs but part of agent observability surface |

### Metrics and network observability

| ID | Severity | Finding | Impact |
| --- | --- | --- | --- |
| T-002 | P1 | `AppSettings.metrics_host` defaults to `"0.0.0.0"`; metrics server starts without authentication | On shared networks, remote clients can scrape operational metrics and invoke metrics MCP resources |
| M-007 | P2 | `MetricsServer` exposes `/metrics` and MCP resources (`metrics://all`) with no authentication | Secondary agent/network surface; Prometheus text uses template URLs in labels (no env values observed) |
| T-004 | P1 (when exposed) | Neither collection MCP nor metrics MCP implement client authentication on Streamable HTTP or legacy SSE | Security depends on bind address and network posture; any reachable client can invoke tools with active-env credentials |

### Persistence adjacent to observability

| ID | Severity | Finding | Impact |
| --- | --- | --- | --- |
| E-001 | P2 | `SensitiveDataMaskingPolicy` masks only `hidden_keys`; non-hidden env values and hardcoded credentials persist resolved in `history.json` | History is an operator-facing audit trail but acts as a cleartext secret store when keys are not marked hidden |
| E-008 | PASS | `HistoryEntry` stores request-side fields only; upstream response bodies are not persisted | Limits third-party PII persistence from responses in on-disk history |
| S-003 | P2 | `AppSettings.alert_webhook_auth_header` persisted in plaintext `settings.json` | Webhook bearer tokens readable by any process with config-directory access |

### Documentation gaps (observability / security)

| Gap | Notes |
| --- | --- |
| Resolved URLs in ERROR logs | No `doc/dev/` guidance on log redaction for HTTP failures (E-003) |
| Metrics bind asymmetry | `metrics_host` default `0.0.0.0` vs `mcp_host` `127.0.0.1` not explained in security terms (T-002) |
| MCP response-body sensitivity | `mcp_secrets_policy.md` does not address full upstream response bodies in tool results (M-002) |
| Network trust model | `mcp_integration.md` does not emphasize no-auth assumption for inbound MCP (T-004) |

**Remediation directions (from audit):** Log template URL or redact query params on HTTP errors (E-003); default metrics bind to localhost (T-002); document network trust model and consider token auth for non-localhost bind (T-004); add response redaction policy for MCP results (M-002); sanitize or omit script `logs` in agent responses (M-003).

**Out of scope per audit:** Penetration testing, formal threat modeling, and new instrumentation were not performed (`30-audit-report.md` § Out of Scope).

## Notes

- Step 5 is verification-only for PYPOST-685; remediation of logging/metrics security gaps belongs in
  Steps 6–7.
- No structured logging, counters, or dashboards were added; existing `RequestService`, MCP,
  metrics-server, and alert instrumentation was inventoried during the audit and left unchanged.
