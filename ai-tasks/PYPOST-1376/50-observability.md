# PYPOST-1376: Observability Implementation

## Verdict

**DECOMPOSE / Jira-only — no product runtime observability changes.**

This ticket delivers decomposition planning Markdown artifacts and creates four granular child Stories under parent epic [PYPOST-1312](https://pypost.atlassian.net/browse/PYPOST-1312). No production `pypost/` Python application runtime code, Qt GUI widgets, MCP server runtime, or database models were modified or introduced within this ticket. Production runtime structured logging, OpenTelemetry spans, Prometheus metrics, Grafana dashboards, and runtime alerting rules are therefore **N/A** for PYPOST-1376 directly.

Observability for this task comprises:
1. **Process Observability**: Top-Down per-step Jira worklog recording, token consumption auditing, and bidirectional ticket traceability.
2. **Downstream Observability Specifications**: Concrete logging taxonomies, structured events, GUI/MCP metrics, and strict zero-leakage redaction audit trails governing child implementation stories ([PYPOST-1377](https://pypost.atlassian.net/browse/PYPOST-1377), [PYPOST-1378](https://pypost.atlassian.net/browse/PYPOST-1378), [PYPOST-1379](https://pypost.atlassian.net/browse/PYPOST-1379), and [PYPOST-1380](https://pypost.atlassian.net/browse/PYPOST-1380)).

---

## Observability Requirements Analysis

| Area | Finding |
| --- | --- |
| Key components | Planning artifacts (`00-roadmap.md`, `10-requirements.md`, `20-architecture.md`, `40-code-cleanup.md`, `50-observability.md`), decomposition notes (`ai-tasks/PYPOST-1312/decomposition-notes.md`), and 4 child Jira issues under PYPOST-1312 |
| Critical paths | Create child Stories in Jira, link parent epic PYPOST-1312, assign to Sprint 2032, verify artifact syntax and links |
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

- Structured logs: N/A (no product code modified in this decomposition task)
- Includes context: N/A for product logs
- Log levels: none added to the application

---

## Metrics Implementation (if applicable)

### Performance Metrics

- **Response time**: N/A — no runtime changes
- **Throughput**: N/A — no runtime changes
- **Error rate**: N/A — no runtime changes

### Business Metrics

N/A for product analytics. Process delivery metric: Epic PYPOST-1312 has been decomposed into 4 cohesive, independently executable child Stories totaling 14 Story Points, all linked to PYPOST-1312 and assigned to Sprint 2032.

### System Health Metrics

- **Resource usage**: N/A — no runtime component
- **Component status**: N/A — no daemon/service instrumentation in scope

---

## Process Observability

Process observability provides an immutable, auditable trail tracking execution effort, token spend, and ticket hierarchy for PYPOST-1376.

### Top-Down Worklogs

Every executed step of PYPOST-1376 records worklogs on [PYPOST-1376](https://pypost.atlassian.net/browse/PYPOST-1376) containing structured metadata:

- `tokens_used`: Monitored token consumption per step
- `role`: Agent execution role (e.g., `execution`)
- `step`: Numeric Top-Down step index (e.g., `1`, `2`, `4`, `5`, `6`)
- `step_name`: Canonical step designation (e.g., `requirements`, `architecture`, `development`, `code_cleanup`, `observability`)

These worklogs provide auditable visibility into autonomous agent progress and resource utilization across the ticket lifecycle.

### Jira Key Traceability

All decomposed provisional IDs map directly to active Jira Stories created in Step 4 under epic [PYPOST-1312](https://pypost.atlassian.net/browse/PYPOST-1312) and active sprint 2032:

| Provisional ID | Jira Key | Summary | Story Points | Sprint | Link |
| --- | --- | --- | :---: | :---: | --- |
| `MASK-1` | `PYPOST-1377` | `[PYPOST-1312] Request model, persistence, and RequestEditor UI for hidden response fields` | 3 | 2032 | [PYPOST-1377](https://pypost.atlassian.net/browse/PYPOST-1377) |
| `MASK-2` | `PYPOST-1378` | `[PYPOST-1312] Permanent MCP output masking for hidden response fields` | 3 | 2032 | [PYPOST-1378](https://pypost.atlassian.net/browse/PYPOST-1378) |
| `MASK-3` | `PYPOST-1379` | `[PYPOST-1312] Interactive click-to-reveal response masking in GUI ResponseView` | 5 | 2032 | [PYPOST-1379](https://pypost.atlassian.net/browse/PYPOST-1379) |
| `MASK-4` | `PYPOST-1380` | `[PYPOST-1312] Integration test suite, edge-case coverage, and developer documentation` | 3 | 2032 | [PYPOST-1380](https://pypost.atlassian.net/browse/PYPOST-1380) |

Parent Epic: [PYPOST-1312](https://pypost.atlassian.net/browse/PYPOST-1312).

---

## Downstream Observability Specifications for Child Stories

While PYPOST-1376 makes zero runtime code changes, child stories PYPOST-1377 through PYPOST-1380 will introduce schema modifications, MCP sanitizer enhancements, Qt GUI interactive spans, and integration suites. To guarantee consistent observability and leak-free operations across those upcoming cycles, the following specifications must be adhered to during their respective Step 6 implementations:

### 1. Structured Log Event Taxonomy

Child stories must emit structured events using PyPost standard loggers (`logging.getLogger("pypost.models.request")`, `logging.getLogger("pypost.mcp.sanitizer")`, or `logging.getLogger("pypost.ui.response_view")`) adhering to standard syslog-compatible levels:

| Event Name | Level | Responsible Ticket | Context Fields | Description |
| --- | --- | --- | --- | --- |
| `request.model.hidden_fields_invalid` | `WARNING` | PYPOST-1377 | `request_id`, `field_count`, `error_detail` | Emitted when deserialization encounters malformed `hidden_response_fields` specifications. |
| `ui.editor.hidden_fields_updated` | `DEBUG` | PYPOST-1377 | `request_id`, `field_count` | Emitted when the user edits configured hidden response field rules in `RequestEditor`. |
| `mcp.response.masking_applied` | `INFO` | PYPOST-1378 | `tool_name`, `request_id`, `masked_field_count` | Emitted when sensitive response fields are permanently masked in an MCP tool response payload. |
| `mcp.response.masking_skipped` | `DEBUG` | PYPOST-1378 | `tool_name`, `request_id`, `reason` | Emitted when response masking is bypassed (e.g. non-JSON payload or no configured hidden fields). |
| `mcp.response.masking_error` | `ERR` | PYPOST-1378 | `tool_name`, `request_id`, `error_type` | Emitted if response sanitization fails; fail-closed sanitization must be enforced. |
| `ui.response.masked_view_initialized` | `DEBUG` | PYPOST-1379 | `masked_count`, `body_bytes` | Emitted when `ResponseView` renders a response body with active masked spans. |
| `ui.response.reveal_toggled` | `INFO` | PYPOST-1379 | `field_path`, `target_state` (`"revealed"` or `"masked"`) | Emitted when the user toggles click-to-reveal for a specific masked field span. |
| `ui.response.mask_fallback_activated` | `WARNING` | PYPOST-1379 | `body_bytes`, `reason` | Emitted when oversized payload fallback (>100KB) bypasses interactive click-to-reveal spans. |
| `test.contract.masking_validated` | `INFO` | PYPOST-1380 | `scenario_name`, `masked_fields_asserted` | Emitted in integration contracts verifying leak-free MCP and GUI assertions. |

### 2. GUI Click-to-Reveal Telemetry & Metrics (PYPOST-1379)

The GUI response viewer must track interaction telemetry without capturing secret values:
- **`gui_reveal_toggles_total` (Counter)**:
  - Labels: `action` (`reveal` | `hide`), `field_type` (`json_key` | `path`).
  - Measures user interaction frequency with sensitive field inspection.
- **`gui_mask_render_duration_seconds` (Histogram)**:
  - Measures overhead of scanning JSON tokens and inserting interactive reveal spans into `FoldableCodeView`.
  - Ensures rendering stays well within interactive frame budgets (<16ms for typical bodies).

### 3. MCP Masking Telemetry & Metrics (PYPOST-1378)

MCP sanitization operates on automated agent boundaries and requires operational metrics:
- **`mcp_masked_responses_total` (Counter)**:
  - Labels: `tool_name`, `has_masked_fields` (`true` | `false`).
  - Tracks total MCP tool executions that evaluated masking rules.
- **`mcp_masked_fields_total` (Counter)**:
  - Labels: `tool_name`.
  - Tracks aggregate count of individual response fields redacted before reaching calling agents.
- **`mcp_sanitizer_duration_seconds` (Histogram)**:
  - Measures latency added to MCP tool execution by the JSON parsing and redaction pipeline.

### 4. Secret Redaction & Audit Trail Safeguards (Zero Cleartext Leakage)

A strict data protection requirement across all four child stories is **zero cleartext secret leakage**:

1. **Strict Field Value Redaction**:
   - Any response field matching a configured `hidden_response_fields` rule must **NEVER** have its raw value logged under any circumstances in application logs, MCP server logs, or crash dumps.
2. **Permitted Log Attributes**:
   - ✅ **Permitted**: `field_name`, `field_path` (e.g. `auth.token`), `masked_field_count`, `is_masked=True`, `value_length=len(val)`.
   - ❌ **Prohibited**: Raw secret strings, prefix/suffix previews (e.g. `ghp_1234...`), or unredacted JSON body dumps in debug logs.
3. **Fail-Closed MCP Redaction**:
   - If an unexpected error occurs while applying masking in `McpResponseSanitizer`, the MCP layer must fail closed (i.e. omit or redact the response body rather than leaking unmasked raw contents to the AI agent).
4. **No UI Reveal Leakage**:
   - UI click-to-reveal events must only record the state transition (`target_state="revealed"`), never the revealed plaintext content.

---

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics — N/A (product scrape unchanged; no new series on this decomposition task)
- [ ] Grafana dashboards — N/A
- [ ] Alerting rules — N/A
- [ ] Log aggregation (ELK, Loki, etc.) — N/A
- [x] Jira worklogs on PYPOST-1376 (step / role / `tokens_used`)
- [x] Traceability mapping (MASK-1..4 → PYPOST-1377 / 1378 / 1379 / 1380 under PYPOST-1312)
- [x] Downstream logging taxonomy, metrics, and secret redaction audit rules defined for child tasks

---

## Validation Results

- [x] Product logs correctly formatted — N/A (zero product code changes)
- [x] Product metrics collected — N/A (none added)
- [x] Logging in error scenarios — N/A (no app logging added)
- [x] Large data structures not logged — N/A (no app logs)
- [x] Metrics available for monitoring — N/A (product scrape unchanged)
- [x] Confirmed zero `pypost/` runtime code modified on this ticket
- [x] Process trail identified: worklogs + child Jira keys under PYPOST-1312 in Sprint 2032
- [x] Downstream observability requirements, telemetry metrics, and secret masking standards formally established
- [x] AI task artifacts verified (`make verify-ai-tasks` passed)
- [x] Static analysis and documentation linting verified (`make lint` passed)

---

## Notes

- STEP 6 is left at `[/]` in `00-roadmap.md` — per `td-roadmap` and step instructions, the executing agent does not mark its own step `[x]`; that is the orchestrator's action after review passes.
- Full runtime observability implementation will be executed by child stories PYPOST-1377 through PYPOST-1380 during their respective Step 6 cycles.
