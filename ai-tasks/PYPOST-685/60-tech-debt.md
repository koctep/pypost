# PYPOST-685: Technical Debt Analysis

**Task type:** Security and secrets handling audit (no application code changes).

**Source:** `30-audit-report.md` — P1/P2/P3 remediation recommendations.

## Shortcuts Taken

- **Static analysis only:** ripgrep call-site inventory, manual flow tracing per
  `20-architecture.md`, and policy doc comparison; no penetration testing, dynamic fuzzing, or
  formal threat modeling.
- **No code fixes in scope:** Findings document residual exposure paths; remediation is deferred
  to follow-up work.
- **Qualitative severity:** P1/P2/P3 ratings are manual exposure assessments without formal
  CVSS scoring or compliance mapping.
- **Documentation gaps deferred:** Missing `doc/dev/` guidance on MCP response-body sensitivity,
  collection-wide tool registration, and `metrics_host` bind asymmetry tracked as follow-ups
  (Step 7 dev docs).

## Code Quality Issues

Documented security exposure gaps in the audited codebase (not introduced by this task):

- **Agent-visible MCP tool results (P1):** `format_structured_tool_result` serializes full
  upstream HTTP response bodies to MCP clients without sanitization (M-002, P-001).
- **Inbound network exposure (P1):** `metrics_host` defaults to `0.0.0.0`; neither MCP server
  surface authenticates clients (T-002, T-004).
- **History and log scope (P2):** Masking applies only to `Environment.hidden_keys`; non-hidden
  env values and hardcoded credentials persist in `history.json`; ERROR logs emit fully resolved
  URLs (E-001, E-003, P-002).
- **Storage scope (P2):** Encryption at rest covers hidden keys only; webhook auth header stored
  plaintext in settings (S-002, S-003).
- **Collection exposure model (P2):** All loaded collections contribute MCP tools when
  `expose_as_mcp=True`; no collection-level ACL beyond the per-request checkbox (C-001).
- **Script logs in MCP results (P2):** Post-script `logs` field can leak env values or response
  fragments to agents (M-003).

## Missing Tests

- No tests were written or modified for this task (audit only).
- **Coverage gaps from audit:** No automated tests assert MCP tool results redact response bodies,
  sanitize script logs, or enforce bind-address defaults. Existing tests confirm hidden-key
  masking on the GUI history path (`test_sensitive_data_masking_policy.py`,
  `test_history_masking_e2e.py`, `test_mcp_secrets_policy.py`) but do not cover agent-visible
  response-body exposure or metrics-server network posture.

## Performance Concerns

None identified. Performance profiling was explicitly out of scope per `10-requirements.md`.

## Follow-up Tasks

Twelve remediation items ticketed in Jira; R-P2-008 resolved in PYPOST-685 Step 7.

### P1 — Critical / high exposure

#### R-P1-001 — Redact MCP tool result response bodies

- **Priority:** P1
- **Recommendation ID:** R-P1-001
- **Finding refs:** M-002, P-001
- **Description:** `format_structured_tool_result` serializes `result.response.body` verbatim
  into JSON text returned to MCP clients. Upstream APIs often echo tokens, session IDs, or PII.
- **Remediation:** Add optional response sanitization/redaction policy for MCP results; consider
  size limits; document that agents see full upstream responses today.
- **Jira:** [PYPOST-703](https://pypost.atlassian.net/browse/PYPOST-703)

#### R-P1-002 — Default metrics bind to localhost

- **Priority:** P1
- **Recommendation ID:** R-P1-002
- **Finding refs:** T-002
- **Description:** `AppSettings.metrics_host` defaults to `"0.0.0.0"`. Metrics server exposes
  Prometheus and metrics MCP on all interfaces without authentication.
- **Remediation:** Default `metrics_host` to `127.0.0.1`; warn or require confirmation when
  binding beyond localhost.
- **Jira:** [PYPOST-704](https://pypost.atlassian.net/browse/PYPOST-704)

#### R-P1-003 — Document or add inbound MCP authentication

- **Priority:** P1
- **Recommendation ID:** R-P1-003
- **Finding refs:** T-004
- **Description:** Neither `MCPServerImpl` nor `MetricsServer` implement client authentication
  on Streamable HTTP or legacy SSE transports. Security depends entirely on bind address and
  network posture.
- **Remediation:** Document network trust model prominently; consider token/auth for
  non-localhost bind.
- **Jira:** [PYPOST-705](https://pypost.atlassian.net/browse/PYPOST-705)

### P2 — Policy gap or secondary surface

#### R-P2-001 — Expand history masking beyond hidden_keys

- **Priority:** P2
- **Recommendation ID:** R-P2-001
- **Finding refs:** E-001, P-002
- **Description:** `SensitiveDataMaskingPolicy` replaces values only for keys in `hidden_keys`.
  Non-hidden env-substituted credentials and hardcoded `Authorization` headers persist verbatim
  in `history.json`.
- **Remediation:** Expand masking heuristics (e.g. `Authorization` header) or stronger operator
  UX for the hidden flag.
- **Jira:** [PYPOST-706](https://pypost.atlassian.net/browse/PYPOST-706)

#### R-P2-002 — Clarify encryption scope for environment variables

- **Priority:** P2
- **Recommendation ID:** R-P2-002
- **Finding refs:** S-002
- **Description:** When encryption is enabled, only `hidden_keys` entries are encrypted;
  non-hidden secrets are written as plain strings to `environments.json`.
- **Remediation:** Settings UX copy clarifying hidden-key-only scope; optional encrypt-all mode
  (product decision).
- **Jira:** [PYPOST-707](https://pypost.atlassian.net/browse/PYPOST-707)

#### R-P2-003 — Protect webhook auth header at rest

- **Priority:** P2
- **Recommendation ID:** R-P2-003
- **Finding refs:** S-003
- **Description:** `AppSettings.alert_webhook_auth_header` is persisted in `settings.json` with
  no encryption or masking.
- **Remediation:** Encrypt or externalize secret storage for webhook credentials.
- **Jira:** [PYPOST-708](https://pypost.atlassian.net/browse/PYPOST-708)

#### R-P2-004 — Redact resolved URLs in HTTPClient error logs

- **Priority:** P2
- **Recommendation ID:** R-P2-004
- **Finding refs:** E-003
- **Description:** On timeout, connection failure, or request exception, `HTTPClient.send_request`
  logs the fully rendered `url` at ERROR level.
- **Remediation:** Log template URL or redact query parameters containing tokens.
- **Jira:** [PYPOST-709](https://pypost.atlassian.net/browse/PYPOST-709)

#### R-P2-005 — Sanitize post-script logs in MCP results

- **Priority:** P2
- **Recommendation ID:** R-P2-005
- **Finding refs:** M-003
- **Description:** When `post_script` runs, `result.script_logs` are included in the MCP tool
  result JSON under `logs`. Scripts can `pypost.log()` env values or response fragments.
- **Remediation:** Sanitize or omit `logs` field for agent responses.
- **Jira:** [PYPOST-710](https://pypost.atlassian.net/browse/PYPOST-710)

#### R-P2-006 — Collection-level MCP exposure control

- **Priority:** P2
- **Recommendation ID:** R-P2-006
- **Finding refs:** C-001
- **Description:** `EnvPresenter._get_mcp_tools` registers all requests with `expose_as_mcp=True`
  across every loaded collection. Operators may believe only the active collection is
  agent-visible.
- **Remediation:** Collection-level MCP gate, active-collection-only registration, or clearer
  UI/docs on global tool catalog scope.
- **Jira:** [PYPOST-711](https://pypost.atlassian.net/browse/PYPOST-711)

#### R-P2-007 — Harden unauthenticated metrics MCP surface

- **Priority:** P2
- **Recommendation ID:** R-P2-007
- **Finding refs:** M-007
- **Description:** `MetricsServer` exposes `/metrics` and MCP resources with no authentication.
  Secondary agent/network surface; lower sensitivity than collection MCP tools.
- **Remediation:** Bind default to localhost (see R-P1-002) plus optional auth for metrics MCP.
- **Jira:** [PYPOST-712](https://pypost.atlassian.net/browse/PYPOST-712)

#### R-P2-008 — Security documentation for MCP and metrics posture

- **Priority:** P2
- **Recommendation ID:** R-P2-008
- **Finding refs:** Documentation alignment table
- **Description:** No `doc/dev/` guidance on MCP response-body sensitivity or collection-wide tool
  registration. `metrics_host` default `0.0.0.0` vs `mcp_host` `127.0.0.1` asymmetry not
  explained in security terms.
- **Remediation:** Add or update dev docs in Step 7; align policy docs with observed behavior.
- **Resolved:** Addressed in PYPOST-685 Step 7 (`doc/dev/security_audit.md`).

### P3 — Low likelihood, documented behavior, or latent risk

#### R-P3-001 — Document plaintext collection storage

- **Priority:** P3
- **Recommendation ID:** R-P3-001
- **Finding refs:** S-005
- **Description:** Request templates in `{data_dir}/collections/` have no encryption. Secrets
  embedded directly in request fields (not env vars) store in cleartext.
- **Remediation:** Operator documentation; expected for a local API client.
- **Jira:** [PYPOST-713](https://pypost.atlassian.net/browse/PYPOST-713)

#### R-P3-002 — Forward hidden_keys if MCP history is added

- **Priority:** P3
- **Recommendation ID:** R-P3-002
- **Finding refs:** M-005
- **Description:** `MCPServerImpl._execute_request_sync` calls `RequestService.execute` without
  `hidden_keys`. Safe today because MCP `RequestService` has no `history_manager`; latent
  footgun if history recording is added to the MCP path.
- **Remediation:** Forward `hidden_keys` when wiring MCP history.
- **Jira:** [PYPOST-714](https://pypost.atlassian.net/browse/PYPOST-714)

#### R-P3-003 — Disable Starlette debug on collection MCP app

- **Priority:** P3
- **Recommendation ID:** R-P3-003
- **Finding refs:** T-005
- **Description:** `MCPServerImpl.create_app` sets `debug=True`, which may surface verbose
  error pages in some deployment contexts.
- **Remediation:** Set `debug=False` for production MCP app.
- **Jira:** [PYPOST-715](https://pypost.atlassian.net/browse/PYPOST-715)

## Blocker Review

**SAFE TO CLOSE** — audit deliverables complete; no application code changes required.
Documented policies largely align with implementation for their stated scope. Twelve follow-up
remediation items ticketed in Jira (PYPOST-703–715); R-P2-008 resolved in Step 7.
