# Security and Secrets Handling Audit

This document summarizes the PyPost security and secrets handling audit (PYPOST-685).
The audit verifies environment storage, UI masking, execution/history/logs, MCP agent
surfaces, transport posture, and collection exposure. It complements the policy docs in
[mcp_secrets_policy.md](mcp_secrets_policy.md),
[sensitive_data_masking_policy.md](sensitive_data_masking_policy.md),
[environment_encryption_at_rest.md](environment_encryption_at_rest.md),
[hidden_variables.md](hidden_variables.md), and
[collection_storage.md](collection_storage.md) (operator guidance for plaintext collections).

## Audit Report

Full report:
[ai-tasks/PYPOST-685/30-audit-report.md](../../ai-tasks/PYPOST-685/30-audit-report.md)

**Date:** 2026-06-12 | **Scope:** Storage, UI masking, execution/history/logs, MCP, transport,
collection exposure, PII persistence

## Executive Summary

Documented secrets policies are **largely implemented** for their stated scope: hidden
environment variables are masked in the env UI, filtered from MCP `list_tools` schemas,
encrypted at rest when encryption is enabled, and masked in persisted request history when
the operator marks keys as hidden. MCP activity logging stores argument **counts** only, not
values. A single code path (`RequestService._record_execution_history`) writes history, always
routing through `SensitiveDataMaskingPolicy` when `hidden_keys` are supplied from the GUI worker
chain.

**Residual exposure concentrates in four areas:**

1. **Agent-visible MCP tool results** — upstream response bodies and post-script logs are
   returned to external MCP clients after `McpResponseSanitizer` redacts hidden values and
   common credential patterns; operators must still treat response content as sensitive.
2. **Inbound network exposure** — metrics server now defaults to `127.0.0.1` and logs a warning
   when bound to a non-loopback address; neither MCP server surface authenticates clients.
3. **History and log scope** — masking applies only to `Environment.hidden_keys`; non-hidden env
   values and hardcoded credentials persist resolved in `history.json`; several DEBUG/ERROR log
   lines emit fully resolved URLs.
4. **Collection exposure model** — before PYPOST-1044, one server aggregated every loaded
   collection. Registry endpoints now expose only their selected collection, but inbound MCP
   remains unauthenticated and request-level `expose_as_mcp` still controls inclusion.

Findings use **P1** (critical/high exposure), **P2** (policy gap or secondary surface),
**P3** (documented behavior, low likelihood, or operator-assumption risk).

## Controls Verified

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

## Key Findings

### Storage and UI

| ID | Finding | Severity |
| --- | --- | --- |
| S-001 | Hidden-variable encryption at rest works as documented | PASS |
| S-002 | Non-hidden environment values always plaintext on disk | P2 |
| S-003 | Settings store webhook auth header in plaintext | P2 |
| S-004 | Hidden-variable UI masking aligned | PASS |
| S-005 | Collections persisted as plaintext JSON — operator guidance in [collection_storage.md](collection_storage.md#security-operator-guidance) | P3 (documented) |

### Execution, History, and Logs

| ID | Finding | Severity |
| --- | --- | --- |
| E-001 | History masking limited to `hidden_keys` | P2 |
| E-002 | Single history write path with masking hook | PASS |
| E-003 | HTTPClient error logs emit resolved URLs | P2 |
| E-004 | History observability logs masked URL at DEBUG | PASS (caveat when `hidden_keys` empty) |
| E-005 | Retry/alert paths use template URL, not resolved | PASS |
| E-006 | Hidden toggle log policy aligned | PASS |
| E-007 | Copy cURL behavior matches documented intent | PASS |
| E-008 | Response bodies not persisted in history | PASS |

### MCP Agent Safety

| ID | Finding | Severity |
| --- | --- | --- |
| M-001 | `list_tools` schema filtering aligned with PYPOST-554 | PASS |
| M-002 | Full upstream response body returned to MCP agents | P1 |
| M-003 | Post-script logs exposed to MCP agents | P2 |
| M-004 | MCP activity log excludes argument values | PASS |
| M-005 | MCP execution does not pass `hidden_keys` (latent) | P3 |
| M-006 | Tool descriptions are operator-controlled static text | PASS |
| M-007 | Metrics MCP surface exposes Prometheus scrape data — localhost default + WARNING on non-loopback bind | P2 (mitigated on loopback) |

### Transport

| ID | Finding | Severity |
| --- | --- | --- |
| T-001 | Outbound HTTP uses requests defaults; TLS verification not disabled | PASS |
| T-002 | Metrics server defaults to all-interfaces bind | P1 |
| T-003 | Collection MCP server defaults to localhost | PASS |
| T-004 | Inbound MCP has no authentication — documented trust model; token auth deferred | P1 (when network-exposed) |
| T-005 | Starlette debug mode enabled on collection MCP app | P3 |

### Collection Exposure

| ID | Finding | Severity |
| --- | --- | --- |
| C-001 | MCP tools span all loaded collections | Remediated by PYPOST-1044: each endpoint selects one collection |
| C-002 | `enable_mcp` is environment-level server gate, not collection ACL | Superseded by explicit endpoint configuration; retained only for migration |
| C-003 | No role-based or multi-user ACL | OUT OF SCOPE |

## Follow-up Work

Twelve prioritized remediation items (3 P1, 8 P2, 3 P3) are listed in
[ai-tasks/PYPOST-685/60-tech-debt.md](../../ai-tasks/PYPOST-685/60-tech-debt.md). Jira tickets
are created by the sprint orchestrator. R-P2-008 (security documentation gaps) was resolved in
PYPOST-685 Step 7.

## Documentation Alignment

| Policy doc | Observed alignment | Gap |
| --- | --- | --- |
| `mcp_secrets_policy.md` | Schema filter + execution merge match code | Does not address response-body exposure in tool results |
| `sensitive_data_masking_policy.md` | History masking for `hidden_keys` matches | Scope is hidden env keys only |
| `environment_encryption_at_rest.md` | Hidden-key-only encryption matches | Operators may misread "encryption enabled" as whole-env |
| `hidden_variables.md` | UI mask + toggle logs match | — |
| `collection_storage.md` | Plaintext persistence and hidden-env guidance match S-005 | — |
| `mcp_integration.md` | Activity log fields, supplier wiring match | Network exposure / no-auth assumption implicit |
| `copy_curl.md` | Active vs history copy behavior matches | — |
| `request_execution.md` | GUI/MCP converge on `RequestService.execute` | MCP omits `hidden_keys` (latent; no history today) |

**Gaps addressed in this step:** developer-facing summary in this document; full findings in the
audit report linked above.

## Related

- [MCP Secrets Policy](mcp_secrets_policy.md)
- [Sensitive Data Masking Policy](sensitive_data_masking_policy.md)
- [Environment Encryption at Rest](environment_encryption_at_rest.md)
- [Hidden Variables](hidden_variables.md)
- [MCP Integration](mcp_integration.md)
- [Request Execution](request_execution.md)
- [Collection Storage](collection_storage.md) — plaintext persistence and operator security
  guidance (S-005 / PYPOST-713)
- [Architecture and Package Boundary Audit](architecture_audit.md)

## Related Audits

Sibling Code Audit summaries — hub:
[documentation_audit.md § Code Audit Hub](documentation_audit.md#code-audit-hub).

- [Architecture and Package Boundary Audit (PYPOST-684)](architecture_audit.md)
- [Test Coverage and Quality Audit (PYPOST-686)](test_audit.md)
- [Code Quality and Maintainability Audit (PYPOST-687)](maintainability_audit.md)
- [Observability and Logging Audit (PYPOST-688)](observability_audit.md)
- [Performance and Scalability Audit (PYPOST-689)](performance_audit.md)
- [Documentation and ADR Alignment Audit (PYPOST-690)](documentation_audit.md)
- [Dependencies and Supply Chain Audit (PYPOST-691)](dependencies_audit.md)
