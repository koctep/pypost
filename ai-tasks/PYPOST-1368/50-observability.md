# PYPOST-1368: Observability Implementation

## Verdict

**DECOMPOSE / Jira-only — no product runtime observability changes.**
This story delivers planning Markdown artifacts and creates four decomposed child Stories under parent epic [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284). No `pypost/` Python application code, Qt widgets, CLI runtime, or daemon processes were modified or added in this ticket. Production runtime structured logging, OpenTelemetry spans, Prometheus metrics, Grafana dashboards, and runtime alerting rules are **N/A** for PYPOST-1368 itself.

Observability for this task consists of **process observability** (Top-Down per-step Jira worklogs, token auditing, and Jira hierarchy mapping) and **downstream observability specifications** governing the target implementation stories ([PYPOST-1372](https://pypost.atlassian.net/browse/PYPOST-1372), [PYPOST-1373](https://pypost.atlassian.net/browse/PYPOST-1373), [PYPOST-1374](https://pypost.atlassian.net/browse/PYPOST-1374), and [PYPOST-1375](https://pypost.atlassian.net/browse/PYPOST-1375)).

---

## Observability Requirements Analysis

| Area | Finding |
| --- | --- |
| Key components | Planning artifacts (`00-roadmap.md`, `10-requirements.md`, `20-architecture.md`, `40-code-cleanup.md`, `50-observability.md`) + 4 child Jira issues under PYPOST-1284 |
| Critical paths | Create child Stories in Jira, link parents to PYPOST-1284, assign to Sprint 2029, verify artifact integrity |
| Product runtime paths | None on this ticket (Step 3 N/A; no product Step 4 code) |
| Performance / health metrics | N/A for product runtime; process audit trail established via per-step Jira worklogs and browse URLs |

---

## Logging Implementation

### Added Logs

None in application / product code.

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

- **Response time**: N/A — no runtime change
- **Throughput**: N/A — no runtime change
- **Error rate**: N/A — no runtime change

### Business Metrics

N/A for product analytics. Process delivery metric: Epic PYPOST-1284 has been decomposed into 4 cohesive, independently executable child Stories totaling 16 Story Points, all linked and assigned to Sprint 2029.

### System Health Metrics

- **Resource usage**: N/A — no runtime component
- **Component status**: N/A — no daemon/service instrumentation in scope

---

## Process Observability

Process observability provides the durable audit trail for tracking execution effort, token spend, and ticket hierarchy for PYPOST-1368.

### Top-Down Worklogs

Every executed step of PYPOST-1368 records worklogs on [PYPOST-1368](https://pypost.atlassian.net/browse/PYPOST-1368) containing structured metadata:

- `tokens_used`: Monitored token consumption per step
- `role`: Agent execution role (e.g., `execution`)
- `step`: Numeric Top-Down step index (e.g., `1`, `2`, `4`, `5`, `6`)
- `step_name`: Canonical step designation (e.g., `requirements`, `architecture`, `development`, `code_cleanup`, `observability`)

These worklogs provide auditable visibility into autonomous agent progress and resource utilization across the ticket lifecycle.

### Jira Key Traceability

All decomposed provisional IDs map directly to active Jira Stories created in Step 4 under epic [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284) and active sprint 2029:

| Provisional ID | Jira Key | Summary | Story Points | Sprint | Link |
| --- | --- | --- | :---: | :---: | --- |
| `WIZARD-1` | `PYPOST-1372` | `[PYPOST-1284] Extend CollectionVariable schema with help_text guidance attribute` | 3 | 2029 | [PYPOST-1372](https://pypost.atlassian.net/browse/PYPOST-1372) |
| `WIZARD-2` | `PYPOST-1373` | `[PYPOST-1284] Implement VariableSetupWizardDialog and expandable VariableGuidanceCard component` | 5 | 2029 | [PYPOST-1373](https://pypost.atlassian.net/browse/PYPOST-1373) |
| `WIZARD-3` | `PYPOST-1374` | `[PYPOST-1284] Integrate variable setup wizard launch and overlay persistence in MCP server editor` | 5 | 2029 | [PYPOST-1374](https://pypost.atlassian.net/browse/PYPOST-1374) |
| `WIZARD-4` | `PYPOST-1375` | `[PYPOST-1284] Add reference collection with OAuth setup guidance and contract test suite` | 3 | 2029 | [PYPOST-1375](https://pypost.atlassian.net/browse/PYPOST-1375) |

Parent Epic: [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284).

---

## Downstream Observability Specifications for Child Stories

While PYPOST-1368 makes zero runtime code changes, child stories PYPOST-1372 through PYPOST-1375 will introduce schema modifications, Qt UI dialogs, and configuration persistence. To guarantee consistent observability across those upcoming cycles, the following specifications must be adhered to during their respective Step 6 implementations:

### 1. Structured Log Event Taxonomy

Child stories must emit structured events using PyPost standard logger (`logging.getLogger("pypost.ui.wizard")` or `logging.getLogger("pypost.models.variable")`) adhering to standard syslog-compatible levels:

| Event Name | Level | Responsible Ticket | Context Fields | Description |
| --- | --- | --- | --- | --- |
| `mcp.wizard.model_validation_failed` | `WARNING` | PYPOST-1372 | `variable_name`, `error_type`, `field` | Emitted when `CollectionVariable` deserialization fails on invalid attributes. |
| `mcp.wizard.launched` | `INFO` | PYPOST-1373 / PYPOST-1374 | `collection_id`, `variable_count`, `required_count` | Emitted when `VariableSetupWizardDialog` is presented to the user. |
| `mcp.wizard.guidance_expanded` | `DEBUG` | PYPOST-1373 | `variable_name` | Emitted when a user expands a `VariableGuidanceCard` guidance panel. |
| `mcp.wizard.input_validation_failed` | `WARNING` | PYPOST-1373 | `missing_required_variables` (list of names) | Emitted when the user attempts to proceed without filling mandatory variables. |
| `mcp.wizard.completed` | `INFO` | PYPOST-1373 / PYPOST-1374 | `collection_id`, `configured_count`, `secret_count` | Emitted when the user confirms wizard values and creates an overlay. |
| `mcp.wizard.cancelled` | `DEBUG` | PYPOST-1373 / PYPOST-1374 | `collection_id` | Emitted when the wizard dialog is dismissed without applying changes. |
| `mcp.overlay.saved` | `INFO` | PYPOST-1374 | `collection_id`, `profile_name`, `keys_updated` | Emitted when local library overlay settings are persisted. |

### 2. Sensitive Field Masking Rules

A critical security and observability requirement for the variable setup subsystem is **zero cleartext secret leakage**:

1. **Strict Key-Level Redaction**: Any variable marked `secret: true` (or matching sensitive keywords such as `token`, `secret`, `password`, `key`, `credential`) must NEVER have its raw value logged under any circumstances.
2. **Safe Log Attributes**: When logging variable states or validation events:
   - ✅ **Permitted**: `variable_name`, `is_secret=True`, `is_set=True/False`, `value_length=len(val)`.
   - ❌ **Prohibited**: Raw secret strings, masked previews exposing prefixes/suffixes (e.g. `ya29.a0...`), or full config dict dumps containing plaintext secrets.
3. **Payload Sanitization**: When debugging or tracing overlay snapshots in logs:
   - Replace secret dictionary values with `"[REDACTED]"`.
4. **No UI State Leakage**: UI logs (such as visibility toggle events) must only record state transition (`echo_mode="Password" -> "Normal"`), never the revealed content.

---

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics — N/A (product scrape unchanged; no new series)
- [ ] Grafana dashboards — N/A
- [ ] Alerting rules — N/A
- [ ] Log aggregation (ELK, Loki, etc.) — N/A
- [x] Jira worklogs on PYPOST-1368 (step / role / `tokens_used`)
- [x] Traceability mapping (WIZARD-1..4 → PYPOST-1372 / 1373 / 1374 / 1375 under PYPOST-1284)
- [x] Downstream logging taxonomy and masking contracts defined for child tasks

---

## Validation Results

- [x] Product logs correctly formatted — N/A (zero product code changes)
- [x] Product metrics collected — N/A (none added)
- [x] Logging in error scenarios — N/A (no app logging added)
- [x] Large data structures not logged — N/A (no app logs)
- [x] Metrics available for monitoring — N/A (product scrape unchanged)
- [x] Confirmed zero `pypost/` runtime code modified on this ticket
- [x] Process trail identified: worklogs + child Jira keys under PYPOST-1284
- [x] Downstream observability requirements and secret masking standards formally established
- [x] AI task artifacts verified (`make verify-ai-tasks` passed)
- [x] Static analysis and documentation linting verified (`make lint` passed)

---

## Notes

- STEP 6 is left at `[/]` in `00-roadmap.md` — per `td-roadmap` and step instructions, the executing agent does not mark its own step `[x]`; that is the orchestrator's action after review passes.
- Full runtime observability implementation will be executed by child stories PYPOST-1372 through PYPOST-1375 during their respective Step 6 cycles.
