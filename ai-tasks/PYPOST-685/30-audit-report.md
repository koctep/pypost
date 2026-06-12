# PYPOST-685: Security and Secrets Handling Audit Report

**Task:** PYPOST-685 — Audit security and secrets handling
**Date:** 2026-06-12
**Scope:** Environment storage, UI masking, execution/history/logs, MCP agent surfaces, transport,
collection exposure, PII persistence
**Baseline:** `doc/dev/mcp_secrets_policy.md`, `sensitive_data_masking_policy.md`,
`environment_encryption_at_rest.md`, `hidden_variables.md`, `mcp_integration.md`,
`copy_curl.md`, `request_execution.md`
**Methodology:** ripgrep call-site inventory, manual flow tracing per `20-architecture.md`,
policy doc comparison, review of existing security tests (`test_sensitive_data_masking_policy.py`,
`test_mcp_secrets_policy.py`, `test_history_masking_e2e.py`, `test_mcp_server_impl.py`). No code
changes.

## Executive Summary

PyPost's **documented secrets policies are largely implemented** for their stated scope: hidden
environment variables are masked in the env UI, filtered from MCP `list_tools` schemas, encrypted
at rest when encryption is enabled, and masked in persisted request history when the operator
marks keys as hidden. MCP activity logging stores argument **counts** only, not values. A single
code path (`RequestService._record_execution_history`) writes history, always routing through
`SensitiveDataMaskingPolicy` when `hidden_keys` are supplied from the GUI worker chain.

**Residual exposure concentrates in four areas:**

1. **Agent-visible MCP tool results** — full upstream HTTP response bodies (and post-script logs)
   are returned to external MCP clients without sanitization.
2. **Inbound network exposure** — metrics MCP defaults to `0.0.0.0`; neither MCP server surface
   authenticates clients.
3. **History and log scope** — masking applies only to `Environment.hidden_keys`; non-hidden env
   values and hardcoded credentials persist resolved in `history.json`; several DEBUG/ERROR log
   lines emit fully resolved URLs.
4. **Collection exposure model** — any request with `expose_as_mcp=True` in **any** loaded
   collection is registered when the active environment has `enable_mcp`; there is no
   collection-level ACL beyond the per-request checkbox.

Findings below use **P1** (critical/high exposure), **P2** (policy gap or secondary surface),
**P3** (documented behavior, low likelihood, or operator-assumption risk).

---

## Storage and UI (AC-2)

### S-001 — Hidden-variable encryption at rest works as documented (PASS)

`EnvironmentVariablesAdapter.serialize_environment` encrypts only keys in
`Environment.hidden_keys` when encryption is enabled; non-hidden values remain plaintext strings
on disk. `EnvironmentSecretsCodec` handles envelope encrypt/decrypt. Error paths log env **name**
and variable **key name**, not values (`environment_value_encrypt_failed`).

**Evidence:** `pypost/core/environment_variables_adapter.py` lines 84–128, 197–218.

**Impact:** Aligns with `environment_encryption_at_rest.md` — operators must mark sensitive keys
as hidden to receive at-rest protection.

### S-002 — Non-hidden environment values always plaintext on disk (P2)

When encryption is enabled, only `hidden_keys` entries are encrypted. A secret stored in a
variable the operator did not mark hidden is written as a plain string to
`{user_data_dir}/environments.json`.

**Evidence:** `environment_variables_adapter.py` lines 93–128 (`else: serialized_variables[key]
= str(value)`).

**Impact:** Operators who enable encryption expecting whole-environment protection may leave
credentials readable on disk and in backups. Remediation: document prominently and/or extend
encryption scope (product decision).

### S-003 — Settings store webhook auth header in plaintext (P2)

`AppSettings.alert_webhook_auth_header` is persisted in `{config_dir}/settings.json` via
`ConfigManager.save_config` with no encryption or masking.

**Evidence:** `pypost/models/settings.py` lines 26–27; `pypost/core/config_manager.py`;
`security_alert_section.py` password-echo UI only masks display, not storage.

**Impact:** Webhook bearer tokens on disk are readable by any process/user with filesystem access
to the PyPost config directory.

### S-004 — Hidden-variable UI masking aligned (PASS)

`environment_variables_widget._make_value_item` displays `HIDDEN_MASK` while storing the real
value in `Qt.ItemDataRole.UserRole`. `VariableHoverHelper` in `mixins.py` masks hover previews
for hidden keys.

**Evidence:** `pypost/ui/widgets/environments/environment_variables_widget.py` lines 133–138;
`pypost/ui/widgets/mixins.py` lines 104–126.

### S-005 — Collections persisted as plaintext JSON (P3)

Request templates (URL, headers, body) in `{data_dir}/collections/` have no encryption. Operators
who embed secrets directly in request fields (not env vars) store them in cleartext.

**Evidence:** `pypost/core/storage.py` — `collections_path`; `RequestData` has no encryption
layer.

**Impact:** Expected for a local API client, but worth documenting as an operator responsibility.

---

## Execution, History, and Logs (AC-3)

### E-001 — History masking limited to `hidden_keys` (P2)

`SensitiveDataMaskingPolicy.build_history_safe_fields` replaces values only for keys in
`hidden_keys`. When `hidden_keys` is empty, resolved URL/headers/body (including env-substituted
credentials) are stored verbatim in `history.json`. Tests explicitly assert non-hidden variables
remain unmasked (`test_non_hidden_variables_remain_unmasked`).

**Evidence:** `pypost/core/sensitive_data_masking_policy.py` lines 33–64;
`tests/test_sensitive_data_masking_policy.py`.

**Impact:** Credentials in env vars not marked hidden, or hardcoded in `Authorization` headers,
persist in history and are copyable via `CurlGenerator.generate_from_history` (masked entries
only apply when hidden keys were present at execution time).

### E-002 — Single history write path with masking hook (PASS)

Only `RequestService._record_execution_history` calls `HistoryManager.append`. GUI execution
forwards `hidden_keys` from `TabsPresenter` → `RequestWorker` → `RequestService.execute`.
MCP-created `RequestService` instances omit `history_manager`, so MCP invocations do not persist
history today.

**Evidence:** grep `HistoryManager.append` — sole caller in `request_service.py` line 354;
`mcp_server_impl._create_request_service` lines 193–199 (no `history_manager`).

### E-003 — HTTPClient error logs emit resolved URLs (P2)

On timeout, connection failure, or request exception, `HTTPClient.send_request` logs the fully
rendered `url` at **ERROR** level. URLs with query tokens or embedded resolved env values appear
in application logs.

**Evidence:** `pypost/core/http_client.py` lines 240, 247, 254.

**Impact:** Support log bundles and shared debug output may contain live credentials from URL
templates.

### E-004 — History observability logs masked URL at DEBUG (PASS with caveat)

`RequestService._emit_history_entry_observability` logs `entry.url` after masking is applied.
When `hidden_keys` is non-empty, logged URL should be safe. When empty, logged URL is fully
resolved (same caveat as E-001).

**Evidence:** `pypost/core/request_service.py` lines 319–327.

### E-005 — Retry/alert paths use template URL, not resolved (PASS)

`retry_exhausted` warnings, `AlertPayload.endpoint`, and `track_request_retry_exhaustion` use
`request.url` (template), not `HTTPClient` resolved fields. Reduces secret leakage in alerts and
Prometheus `endpoint` labels.

**Evidence:** `request_service.py` lines 367–377, 383; `alert_manager.py` `AlertPayload`.

### E-006 — Hidden toggle log policy aligned (PASS)

`HiddenToggleLogPolicy.format_key_name` redacts key names unless
`AppSettings.log_hidden_key_names` is true. Env dialog receives the setting snapshot at open time.

**Evidence:** `pypost/core/hidden_toggle_log_policy.py`; `env_presenter._open_env_manager`.

### E-007 — Copy cURL behavior matches documented intent (PASS)

Active-request copy uses `CurlGenerator.generate` with real env values (operator-intended).
History copy uses `generate_from_history` on already-masked entries when hidden keys were used.

**Evidence:** `doc/dev/copy_curl.md`; `curl_generator.py`.

### E-008 — Response bodies not persisted in history (PASS)

`HistoryEntry` stores request-side fields only (url, headers, body, status, timing). Upstream
response bodies are not written to `history.json`, limiting third-party PII persistence from
responses.

**Evidence:** `pypost/models/models.py` `HistoryEntry` definition.

---

## MCP Agent Safety (AC-4)

### M-001 — `list_tools` schema filtering aligned with PYPOST-554 (PASS)

`MCPServerImpl._generate_schema` calls `McpSecretsPolicy.filter_agent_param_specs`, removing
env-only and hidden keys from agent-visible `inputSchema`. Execution merges real env values at
`call_tool` via `execution_environment_variables` and `_merge_execution_variables`. DEBUG logs
use count-only `safe_execution_log_fields`.

**Evidence:** `mcp_server_impl.py` lines 175–191, 213–220; `mcp_secrets_policy.py`;
`tests/test_mcp_secrets_policy.py`.

### M-002 — Full upstream response body returned to MCP agents (P1)

`format_structured_tool_result` serializes `result.response.body` verbatim into the JSON text
returned to MCP clients. Upstream APIs often echo tokens, session IDs, or PII in response bodies.

**Evidence:** `mcp_server_impl.py` lines 48–60, 120–145.

**Impact:** External agents receive data beyond the operator/agent contract boundary established
for `list_tools` schemas. This is the highest-risk agent-visible leakage path for credential
echo and third-party PII.

**Remediation direction:** Add optional response sanitization/redaction policy for MCP results;
document that agents see full upstream responses today.

### M-003 — Post-script logs exposed to MCP agents (P2)

When `post_script` runs, `result.script_logs` are included in the MCP tool result JSON under
`logs`. Scripts can `pypost.log()` env values or response fragments.

**Evidence:** `mcp_server_impl.py` lines 55–56; `script_executor.py` `ScriptContext.log`.

**Impact:** Operator-written scripts can unintentionally return secrets to agents.

### M-004 — MCP activity log excludes argument values (PASS)

`McpActivityEntry` stores `mcp_arg_count` but not argument keys or values. Matches
`mcp_integration.md` activity table.

**Evidence:** `mcp_activity_log.py`; `mcp_server_impl.py` lines 130–142.

### M-005 — MCP execution does not pass `hidden_keys` to `execute` (P3 — latent)

`MCPServerImpl._execute_request_sync` calls `RequestService.execute` without `hidden_keys`.
Currently safe because MCP `RequestService` has no `history_manager`. If history recording is
added to the MCP path without forwarding `hidden_keys`, hidden values would persist unmasked.

**Evidence:** `mcp_server_impl.py` lines 201–203.

**Impact:** Architectural footgun; no active leakage today.

### M-006 — Tool descriptions are operator-controlled static text (PASS)

`tool_description` returns `mcp_description` or request `name` — not template-rendered env
values.

**Evidence:** `mcp_tool_contract.py` lines 19–24.

### M-007 — Metrics MCP surface exposes Prometheus scrape data (P2)

`MetricsServer` exposes `/metrics` and MCP resources (`metrics://all`) with no authentication.
Prometheus text includes counters and labels (e.g. `endpoint` on retry exhaustion uses template
URLs). No env values observed in metric definitions.

**Evidence:** `metrics_server.py`; `metrics_registry.py`.

**Impact:** Secondary agent/network surface; lower sensitivity than collection MCP tools but still
unauthenticated.

---

## Transport (AC-5)

### T-001 — Outbound HTTP uses requests defaults; TLS verification not disabled (PASS)

`HTTPClient` uses `requests.Session.request` with no `verify=False`. No product code overrides
TLS verification. Cleartext `http://` URLs are operator-configured.

**Evidence:** grep `verify=False` — no matches in `pypost/`; `http_client.py` line 238.

**Impact:** Product relies on operator URL choice and system CA trust store.

### T-002 — Metrics server defaults to all-interfaces bind (P1)

`AppSettings.metrics_host` defaults to `"0.0.0.0"`. `main.py` starts the metrics server with
this default, exposing Prometheus and metrics MCP on all interfaces without authentication.

**Evidence:** `pypost/models/settings.py` line 24; `pypost/main.py` line 32.

**Impact:** On shared networks, unauthenticated remote clients can scrape operational metrics and
invoke metrics MCP resources. Contrast: `mcp_host` defaults to `127.0.0.1`.

**Remediation direction:** Default `metrics_host` to `127.0.0.1` or require explicit confirmation
when binding beyond localhost.

### T-003 — Collection MCP server defaults to localhost (PASS)

`mcp_host` defaults to `127.0.0.1`. `bind_address_validation` allows `0.0.0.0` and hostnames
when the operator configures wider bind.

**Evidence:** `models/settings.py` line 22; `bind_address_validation.py`.

### T-004 — Inbound MCP has no authentication (P1 when network-exposed)

Neither `MCPServerImpl` nor `MetricsServer` implement client authentication on Streamable HTTP
or legacy SSE transports. Security depends entirely on bind address and network posture.

**Evidence:** `mcp_streamable_http.py`, `mcp_legacy_sse.py` — no auth middleware; grep `auth` in
transport modules — no matches.

**Impact:** Any client that can reach the bind address can invoke exposed collection tools with
the operator's active environment credentials merged at execution time.

### T-005 — Starlette debug mode enabled on collection MCP app (P3)

`MCPServerImpl.create_app` sets `debug=True`, which may surface verbose error pages in some
deployment contexts.

**Evidence:** `mcp_server_impl.py` line 225.

---

## Collection Exposure (AC-6)

### C-001 — MCP tools span all loaded collections (P2)

`EnvPresenter._get_mcp_tools` iterates every collection from `RequestManager.get_collections()`
and registers all requests where `expose_as_mcp=True`. There is no per-collection enable flag
beyond the per-request checkbox. Switching environments changes **which secrets are merged** but
not **which tools exist**.

**Evidence:** `env_presenter.py` lines 441–447; `mcp_server_impl.register_tools` lines 205–210.

**Impact:** Operators may believe only the "active" collection is agent-visible; in reality all
flagged requests across all collections are callable. An agent can invoke a sensitive admin
endpoint exposed in a different collection while the operator works in another.

**Remediation direction:** Collection-level MCP gate, active-collection-only registration, or
clearer UI/docs on global tool catalog scope.

### C-002 — `enable_mcp` is environment-level server gate, not collection ACL (PASS — document)

MCP server starts only when the selected `Environment.enable_mcp` is true. This controls server
lifecycle, not which collections contribute tools.

**Evidence:** `env_presenter._on_env_changed` lines 305–314.

### C-003 — No role-based or multi-user ACL (OUT OF SCOPE — noted)

The product has no RBAC. Effective "ACL" is: (1) `expose_as_mcp` per request, (2) `enable_mcp`
per environment, (3) network bind settings. Audit confirms this matches requirements scope.

---

## PII and Sensitive Data

### P-001 — Third-party PII in MCP tool results (P1)

See M-002. Response bodies from third-party APIs may contain user emails, names, or account data
returned to MCP agents and visible in agent conversation history.

### P-002 — Request-side PII in history when not hidden (P2)

See E-001. Request bodies with PII in non-hidden template variables persist in `history.json`.

### P-003 — SSE probe truncates event data in response summary (PASS)

SSE handling summarizes events with 100-char truncation for probe display; full stream not stored
in history.

**Evidence:** `http_client.py` `_handle_sse_response` lines 171–173.

---

## Documentation Alignment (AC-7)

| Policy doc | Observed alignment | Gap |
| --- | --- | --- |
| `mcp_secrets_policy.md` | Schema filter + execution merge match code | Does not address response-body exposure in tool results |
| `sensitive_data_masking_policy.md` | History masking for `hidden_keys` matches | Scope is hidden env keys only; non-hidden credentials not mentioned as out-of-scope risk |
| `environment_encryption_at_rest.md` | Hidden-key-only encryption matches | Operators may misread "encryption enabled" as whole-env |
| `hidden_variables.md` | UI mask + toggle logs match | — |
| `mcp_integration.md` | Activity log fields, supplier wiring match | Network exposure / no-auth assumption implicit, not emphasized |
| `copy_curl.md` | Active vs history copy behavior matches | — |
| `request_execution.md` | GUI/MCP converge on `RequestService.execute` | MCP omits `hidden_keys` (latent; no history today) |

**Stale/missing documentation:**

- No `doc/dev/` guidance on MCP response-body sensitivity or collection-wide tool registration.
- `metrics_host` default `0.0.0.0` vs `mcp_host` `127.0.0.1` asymmetry not explained in security
  terms.

---

## Prioritized Recommendations (AC-8)

| Priority | ID | Finding | Remediation direction |
| --- | --- | --- | --- |
| **P1** | M-002 / P-001 | Full response body in MCP tool results | Response redaction policy for agent results; size limits; document current behavior |
| **P1** | T-002 | Metrics bind `0.0.0.0` default | Default to localhost; warn on wide bind |
| **P1** | T-004 | No inbound MCP authentication | Document network trust model; consider token/auth for non-localhost bind |
| **P2** | E-001 | History stores non-hidden credentials | Expand masking heuristics (e.g. `Authorization` header) or stronger operator UX for hidden flag |
| **P2** | S-002 | Encryption scope is hidden keys only | Settings UX copy; optional encrypt-all mode |
| **P2** | S-003 | Webhook auth in plaintext settings | Encrypt or externalize secret storage |
| **P2** | E-003 | Resolved URLs in ERROR logs | Log template URL or redact query params |
| **P2** | M-003 | Script logs in MCP results | Sanitize or omit `logs` field for agent responses |
| **P2** | C-001 | All collections contribute MCP tools | Collection-level exposure control or active-collection filter |
| **P2** | M-007 | Unauthenticated metrics MCP | Bind default + optional auth |
| **P3** | S-005 | Plaintext collections | Operator documentation |
| **P3** | M-005 | MCP path omits `hidden_keys` | Forward `hidden_keys` if MCP history added |
| **P3** | T-005 | Starlette debug=True | Set `debug=False` for production MCP app |

Step 6 (`60-tech-debt.md`) should create Jira Debt issues for P1 and agreed P2 items (AC-9).

---

## Controls Verified (Summary)

| Control | Status |
| --- | --- |
| Hidden env UI masking | Aligned |
| MCP `list_tools` schema filtering | Aligned |
| Hidden env encryption at rest | Aligned (hidden keys only) |
| History masking for hidden keys (GUI path) | Aligned |
| MCP activity log (no arg values) | Aligned |
| MCP execution env merge (real hidden values) | Aligned |
| Async env storage gateway logging | No decrypted values logged |
| TLS verify disabled in code | Not present |
| Outbound response in history | Not persisted |

---

## Out of Scope

Per `10-requirements.md` and `20-architecture.md`:

- Code fixes or refactors (this step is read-only)
- Penetration testing, formal threat modeling, compliance certification
- Full PYPOST-684 package-boundary re-audit (cross-referenced only where secrets cross layers)
- Performance, general UI/UX, dependency upgrades
- Multi-user RBAC (not present in product)

---

## Methodology Notes

### Call-site inventory (grep)

| Pattern | Primary modules |
| --- | --- |
| `hidden_keys` | `request_service`, `worker`, `tabs_presenter`, `env_presenter`, `mcp_server_impl`, `environment_variables_adapter` |
| `HIDDEN_MASK` / `HIDDEN_PLACEHOLDER` | `constants`, `mixins`, `environment_variables_widget`, `sensitive_data_masking_policy` |
| `expose_as_mcp` | `request_editor`, `env_presenter`, `mcp_server_impl`, `mcp_tools_overview` |

### Persistence paths

| Artifact | Path |
| --- | --- |
| Environments | `{user_data_dir}/environments.json` |
| Collections | `{user_data_dir}/collections/` |
| Settings | `{config_dir}/settings.json` |
| History | `{user_data_dir}/history.json` |
| Alert log | `{user_data_dir}/pypost-alerts.log` (optional) |

### Tests reviewed

`test_sensitive_data_masking_policy.py`, `test_mcp_secrets_policy.py`,
`test_history_masking_e2e.py`, `test_mcp_server_impl.py`, `test_mcp_activity_log.py`,
`test_environment_secrets_codec.py`
