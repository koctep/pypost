# PYPOST-1186: Observability Implementation

## Verdict

**N/A — no new production observability.** This task consolidates three
Key/Value empty-row table copies into one shared Qt widget
(`EmptyRowKeyValueTable`) plus thin named wrappers. There is no new
service, presenter, or network path. Editing table cells must not log
header keys or values (secrets / auth tokens).

## Observability Requirements Analysis

| Area | Finding |
| ---- | ------- |
| Key components changed | UI widgets only: shared `empty_row_key_value_table.py`; thin wrappers in `request_editor`, `websocket/connection_editor`, `mcp_client/headers_table` |
| Critical production paths | Unchanged at the wire/presenter layer — HTTP send, WS connect lock, MCP `resolve_outbound_fields` / service `header_count` remain prior stories |
| Performance / business metrics | Not applicable — no new user-facing throughput or conversion surface |

Product observability for MCP outbound headers (DEBUG count-only resolve,
service `header_count`) was delivered under PYPOST-1167 / PYPOST-1173 and
is outside this extract. CI regression signal for this ticket is the green
shared-ancestry / strip / FR-5 suite, not new runtime telemetry.

## Logging Implementation

### Added Logs

No production logs added on the shared table or wrappers. Logging header
maps from `get_data` / `set_data` / `itemChanged` would risk leaking
secrets and was explicitly rejected.

- **EMERG**: N/A
- **ALERT**: N/A
- **CRIT**: N/A
- **ERR**: N/A
- **WARNING**: N/A
- **NOTICE**: N/A
- **INFO**: N/A
- **DEBUG**: N/A

Existing MCP Client presenter / service header-count logs remain unchanged
and must stay count-only (no keys/values).

### Log Structure

Log format used:

- Structured logs: N/A (no new logs)
- Includes context: N/A
- Log levels: none added

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:

- **Response time**: N/A
- **Throughput**: N/A
- **Error rate**: N/A

### Business Metrics

Business metrics:

- N/A — widget consolidation is not a conversion event

### System Health Metrics

System health metrics:

- **Resource usage**: N/A
- **Component status**: N/A

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics — no new series
- [ ] Grafana dashboards — no new dashboard
- [ ] Alerting rules — N/A
- [ ] Log aggregation — no new logger events from this extract

Catalog updates for `doc/dev/logging.md` are not required (no new events).

## Validation Results

Validation results:

- [x] Logs are correctly formatted — N/A (none added)
- [x] Metrics are collected correctly — N/A (none added)
- [x] Logging works in error scenarios — N/A; widget errors surface as
  Qt/UI behavior, not logger events
- [x] Large data structures are not logged — table maps never logged
- [x] Metrics are available for monitoring — unchanged prior MCP/HTTP
  metrics only

## Notes

- Deliberately **no** `itemChanged` / `get_data` / `set_data` debug logs:
  Key/Value cells often hold `Authorization` and env-templated secrets.
- WS `set_read_only` while connected remains a UI edit-trigger toggle
  with no observability event (same as before the extract).
- STEP 6 is left `[/]` in `00-roadmap.md` — the executing agent does not
  mark `[x]`.
