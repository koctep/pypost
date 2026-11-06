# PYPOST-1339: Observability Implementation

## Observability applicability

**N/A — no production logging or metrics added.**

This task is scoped to offline MCP example-collection verification only:

- Correct surviving-template-marker checks in
  `tests/test_github_mcp_collection.py` and `tests/test_gitlab_mcp_collection.py`
  so body inspection uses `_render(request.body, …)` text instead of
  `json.dumps(parsed)`.
- Twin coverage that a nested-object final body field does not false-positive.
- Optional field-order restore in `examples/collections/github_mcp.json`
  (`ref` then `inputs` on `github_dispatch_workflow`).

No `pypost/` runtime modules, request execution paths, or shipping services were
changed. There is no production execution surface whose health, latency, or
error rate would be improved by new structured logs or metrics for this debt.

Pytest assertions and `make test` remain the observability for this gate: a
leftover marker or false-positive scan failure surfaces as a failed CI/test run,
not as an operational signal.

## Logging Implementation

### Added Logs

No production logs added.

- **EMERG**: N/A
- **ALERT**: N/A
- **CRIT**: N/A
- **ERR**: N/A
- **WARNING**: N/A
- **NOTICE**: N/A
- **INFO**: N/A
- **DEBUG**: N/A

### Log Structure

Log format used:
- Structured logs: N/A
- Includes context: N/A
- Log levels: none added

## Metrics Implementation (if applicable)

### Performance Metrics

No performance metrics added:
- **Response time**: N/A
- **Throughput**: N/A
- **Error rate**: N/A

### Business Metrics

Business metrics:
- N/A — no production business counters for this test-only change

### System Health Metrics

System health metrics:
- **Resource usage**: N/A
- **Component status**: N/A

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

None applicable; unchecked by design.

## Validation Results

Validation results:
- [x] Logs are correctly formatted — N/A (none added)
- [x] Metrics are collected correctly — N/A (none added)
- [x] Logging works in error scenarios — N/A (failures are pytest assertions)
- [x] Large data structures are not logged — N/A (no new log sites)
- [x] Metrics are available for monitoring — N/A

## Notes

- Parent debt: PYPOST-1334 TD-1; sibling shared-helper extraction remains
  PYPOST-1340 / TD-2 (out of scope).
- If a future task moves marker scanning into a shared runtime helper used by
  production MCP tooling, re-evaluate Step 6 for that helper’s error paths and
  call volume. That work is not part of PYPOST-1339.
