# PYPOST-1408: Observability Implementation

## Verdict

**DECOMPOSE / Jira-only — no product runtime observability changes.**

This ticket delivers decomposition planning Markdown artifacts and creates four granular child
Stories under parent epic [PYPOST-1407](https://pypost.atlassian.net/browse/PYPOST-1407). No production
`pypost/` Python application runtime code, Qt GUI widgets, MCP server daemon runtime, or database
models were modified or introduced within this ticket. Production runtime structured logging,
OpenTelemetry spans, Prometheus metrics, Grafana dashboards, and runtime alerting rules are
therefore **N/A** for PYPOST-1408 directly.

Observability for this task comprises:
1. **Process Observability**: Top-Down per-step Jira worklog recording, token consumption auditing,
   and bidirectional ticket traceability.
2. **Downstream Observability Specifications**: Concrete logging taxonomies, structured events,
   lifecycle metrics, and strict zero-leakage redaction audit trails governing child implementation
   stories ([PYPOST-1409](https://pypost.atlassian.net/browse/PYPOST-1409),
   [PYPOST-1410](https://pypost.atlassian.net/browse/PYPOST-1410),
   [PYPOST-1411](https://pypost.atlassian.net/browse/PYPOST-1411), and
   [PYPOST-1412](https://pypost.atlassian.net/browse/PYPOST-1412)).

---

## Observability Requirements Analysis

| Area | Finding |
| --- | --- |
| Key components | Planning artifacts (`00-roadmap.md`, `10-requirements.md`, `20-architecture.md`, `40-code-cleanup.md`, `50-observability.md`), decomposition notes (`ai-tasks/PYPOST-1407/decomposition-notes.md`), and 4 child Jira issues under PYPOST-1407 |
| Critical paths | Create child Stories in Jira, link parent epic PYPOST-1407, assign to Sprint 2033, verify artifact syntax and links |
| Product runtime paths | None on this ticket (Step 3 N/A; no product runtime code in Step 4) |
| Performance / health metrics | N/A for product runtime; process audit trail established via per-step Jira worklogs and browse URLs |

---

## Logging Implementation

### Added Logs

None in application / product code for this decomposition task.

- **EMERG**: N/A — no production runtime component
- **ALERT**: N/A — no runtime alerting path
- **CRIT**: N/A — no operational runtime path
- **ERR**: N/A — product exception logging unchanged
- **WARNING**: N/A — no runtime warning emissions
- **NOTICE**: N/A — no runtime event notifications
- **INFO**: N/A — no runtime informational logging
- **DEBUG**: N/A — no runtime debug logging

### Log Structure

Log format used:
- Structured logs: N/A (no product code modified in this decomposition task)
- Includes context: N/A for product logs
- Log levels: none added to the application

---

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:
- **Response time**: N/A — no runtime changes
- **Throughput**: N/A — no runtime changes
- **Error rate**: N/A — no runtime changes

### Business Metrics

Business metrics:
- N/A for product runtime analytics.
- **Process delivery metric**: Epic PYPOST-1407 has been decomposed into 4 cohesive, independently
  executable child Stories totaling 14 Story Points, all linked to parent PYPOST-1407 and assigned
  to Sprint 2033.

### System Health Metrics

System health metrics:
- **Resource usage**: N/A — no runtime component
- **Component status**: N/A — no daemon/service instrumentation in scope

---

## Process Observability

Process observability provides an immutable, auditable trail tracking execution effort, token
spend, and ticket hierarchy for PYPOST-1408.

### Top-Down Worklogs

Every executed step of PYPOST-1408 records worklogs on [PYPOST-1408](https://pypost.atlassian.net/browse/PYPOST-1408)
containing structured metadata:
- `tokens_used`: Monitored token consumption per step
- `role`: Agent execution role (`execution`)
- `step`: Numeric Top-Down step index (`1`, `2`, `4`, `5`, `6`)
- `step_name`: Canonical step designation (`requirements`, `architecture`, `development`, `code_cleanup`, `observability`)

These worklogs provide auditable visibility into autonomous agent progress and resource utilization
across the ticket lifecycle.

### Bidirectional Jira Traceability

All decomposed provisional IDs map directly to active Jira Stories created in Step 4 under parent
epic [PYPOST-1407](https://pypost.atlassian.net/browse/PYPOST-1407) and assigned to active Sprint 2033:

| Provisional ID | Jira Key | Summary | Story Points | Sprint | Link |
| --- | --- | --- | :---: | :---: | --- |
| `COLVAR-1` | `PYPOST-1409` | `[PYPOST-1407] Eliminate library-level variables and establish collection-scoped variables and catalog manifest` | 3 | 2033 | [PYPOST-1409](https://pypost.atlassian.net/browse/PYPOST-1409) |
| `COLVAR-2` | `PYPOST-1410` | `[PYPOST-1407] Standalone MCP server configuration and execution without workspace environment` | 5 | 2033 | [PYPOST-1410](https://pypost.atlassian.net/browse/PYPOST-1410) |
| `COLVAR-3` | `PYPOST-1411` | `[PYPOST-1407] Workspace environment variable import action from collections` | 3 | 2033 | [PYPOST-1411](https://pypost.atlassian.net/browse/PYPOST-1411) |
| `COLVAR-4` | `PYPOST-1412` | `[PYPOST-1407] Integration test suite, compatibility matrix, and developer documentation` | 3 | 2033 | [PYPOST-1412](https://pypost.atlassian.net/browse/PYPOST-1412) |

- **Parent Epic Link**: [PYPOST-1407](https://pypost.atlassian.net/browse/PYPOST-1407) (Collection-scoped variables for standalone MCP servers and workspace collection import)
- **Sprint Linkage**: Sprint 2033 (Collection-Scoped Variables)
- **Bidirectional Traceability**: PYPOST-1408 decomposes PYPOST-1407; child tasks PYPOST-1409..1412 link back to parent PYPOST-1407.

---

## Downstream Observability Specifications for Child Stories

While PYPOST-1408 makes zero runtime code changes, child stories PYPOST-1409 through PYPOST-1412
will introduce manifest schema updates, standalone MCP server runtime management, GUI import
actions, and end-to-end integration test suites. To guarantee consistent observability and leak-free
operations across those upcoming implementation cycles, the following specifications must be
adhered to during their respective Step 6 implementations:

### 1. Structured Log Event Taxonomy

Child stories must emit structured events using PyPost standard loggers (`logging.getLogger("pypost.core.library")`,
`logging.getLogger("pypost.mcp.controller")`, `logging.getLogger("pypost.ui.environment")`, or
`logging.getLogger("pypost.core.resolver")`) adhering to standard syslog-compatible levels:

| Event Name | Level | Responsible Ticket | Context Fields | Description |
| --- | --- | --- | --- | --- |
| `library.manifest.catalog_loaded` | `INFO` | PYPOST-1409 | `manifest_path`, `collection_count`, `version` | Emitted when a catalog manifest is successfully parsed without library variables. |
| `library.manifest.legacy_detected` | `WARNING` | PYPOST-1409 | `manifest_path`, `deprecated_keys` | Emitted when backward-compatibility parser encounters legacy library-level variables/presets. |
| `library.manifest.schema_invalid` | `ERR` | PYPOST-1409 | `manifest_path`, `error_detail` | Emitted when manifest YAML/JSON fails catalog schema validation. |
| `collection.variable.resolved` | `DEBUG` | PYPOST-1409 | `collection_id`, `variable_count`, `preset_name` | Emitted when collection variables and presets are resolved for runtime use. |
| `mcp.server.standalone_configured` | `INFO` | PYPOST-1410 | `server_name`, `collection_id`, `has_preset` | Emitted when a standalone MCP server is configured without workspace environment. |
| `mcp.server.standalone_started` | `NOTICE` | PYPOST-1410 | `server_id`, `pid`, `collection_id` | Emitted when standalone server process is spawned and starts listening. |
| `mcp.server.variable_unsatisfied` | `ERR` | PYPOST-1410 | `server_id`, `variable_name` | Emitted when required collection variable lacks default or preset value. |
| `mcp.server.standalone_terminated` | `INFO` | PYPOST-1410 | `server_id`, `exit_code`, `uptime_seconds` | Emitted upon normal or abrupt server process termination. |
| `ui.env_import.dialog_opened` | `DEBUG` | PYPOST-1411 | `source_collection_id`, `target_env_id` | Emitted when variable import dialog opens from environment view. |
| `ui.env_import.completed` | `INFO` | PYPOST-1411 | `imported_count`, `overwritten_count`, `skipped_count` | Emitted when collection variable import completes successfully. |
| `ui.env_import.conflict_detected` | `WARNING` | PYPOST-1411 | `variable_name`, `policy` | Emitted when imported variable collides with an existing environment variable. |
| `test.contract.standalone_mcp_verified` | `INFO` | PYPOST-1412 | `collection_id`, `server_status` | Emitted in contract tests verifying standalone MCP execution without workspace env. |
| `test.contract.env_import_verified` | `INFO` | PYPOST-1412 | `variable_count`, `secrets_flagged` | Emitted in contract tests verifying environment variable import. |

### 2. Standalone MCP Server Telemetry & Metrics (PYPOST-1410)

The standalone MCP server controller requires operational metrics to monitor runtime health:
- **`pypost_standalone_mcp_servers_started_total` (Counter)**:
  - Labels: `collection_id`, `preset_configured` (`true` | `false`).
  - Tracks total number of standalone MCP server startup attempts.
- **`pypost_standalone_mcp_server_start_duration_seconds` (Histogram)**:
  - Measures latency from server spawn to operational readiness.
- **`pypost_standalone_mcp_server_errors_total` (Counter)**:
  - Labels: `collection_id`, `error_type` (`missing_variable`, `spawn_failure`, `exit_nonzero`).
  - Measures operational errors during standalone server lifecycle.
- **`pypost_active_standalone_mcp_servers` (Gauge)**:
  - Measures currently active running standalone MCP server processes.

### 3. Collection Variable Import Telemetry & Metrics (PYPOST-1411)

Environment variable import operations track adoption and conflict resolution:
- **`pypost_collection_variable_imports_total` (Counter)**:
  - Labels: `conflict_policy` (`skip`, `overwrite`, `prompt`).
  - Tracks total import operations performed across workspace environments.
- **`pypost_collection_variables_imported_total` (Counter)**:
  - Labels: `is_secret` (`true` | `false`).
  - Tracks aggregate count of imported variables, monitoring secret vs. plain variable adoption.

### 4. Secret Redaction & Audit Trail Safeguards (Zero Cleartext Leakage)

A strict security and data hygiene requirement across all four child stories is **zero cleartext secret leakage**:

1. **Strict Value Redaction**:
   - Any collection variable designated as `secret: true` must **never** have its raw value logged, dumped to debug files, or exposed in telemetry labels.
2. **Permitted Log Attributes**:
   - ✅ **Permitted**: `variable_name`, `variable_type`, `is_secret=True`, `value_length=len(val)`, `source` (`"preset"` or `"overlay"`).
   - ❌ **Prohibited**: Raw secret strings, auth tokens, API keys, or full environment variable dictionaries containing secret values.
3. **Environment Import Secret Preservation**:
   - When importing collection variables into workspace environments, `secret: true` flags must automatically map to `hidden: true` in the target workspace environment model.
4. **Standalone MCP Subprocess Safety**:
   - Sensitive environment variables passed to the standalone MCP server process must be injected securely via process environment or stdin pipe without echoing onto CLI logs or shell execution history.

---

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics — N/A (product scrape unchanged; no new series on this decomposition task)
- [ ] Grafana dashboards — N/A
- [ ] Alerting rules — N/A
- [ ] Log aggregation (ELK, Loki, etc.) — N/A
- [x] Jira worklogs on PYPOST-1408 (step / role / `tokens_used`)
- [x] Traceability mapping (COLVAR-1..4 → PYPOST-1409 / 1410 / 1411 / 1412 under PYPOST-1407)
- [x] Downstream logging taxonomy, metrics, and secret redaction audit rules defined for child tasks

---

## Validation Results

Validation results:

- [x] Logs are correctly formatted — N/A (zero product code changes)
- [x] Metrics are collected correctly — N/A (none added to application)
- [x] Logging works in error scenarios — N/A (no app logging added)
- [x] Large data structures are not logged — N/A (no app logs)
- [x] Metrics are available for monitoring — N/A (product scrape unchanged)
- [x] Confirmed zero `pypost/` runtime code modified on this ticket
- [x] Process trail identified: worklogs + child Jira keys under PYPOST-1407 in Sprint 2033
- [x] Downstream observability requirements, telemetry metrics, and secret masking standards formally established
- [x] AI task artifacts verified (`make verify-ai-tasks` passed)
- [x] Static analysis and documentation linting verified (`make lint` passed)

---

## Notes

- STEP 6 is left at `[/]` in `00-roadmap.md` — per `td-roadmap` and step instructions, the executing
  agent does not mark its own step `[x]`; that is the orchestrator's action after review passes.
- Full runtime observability implementation will be executed by child stories PYPOST-1409 through
  PYPOST-1412 during their respective Step 6 cycles.
