# PYPOST-1050: Observability Implementation

## Verdict

**N/A for production logging and metrics — offline fixture-contract tests and example documentation only.**
This story documents the Jira Agile ≤50 backlog batch size limit on the `jira-move-issues-to-backlog` tool description (`examples/collections/jira_mcp.json`), documents the constraint in `examples/README.md`, and locks the `"50"` discoverability substring in `tests/test_example_fixtures.py`. No application packages under `pypost/`, request send paths, MCP handlers, logging calls, or Prometheus instruments were added or changed.

Observability for this deliverable is provided at development and CI time through **diagnostic pytest assertion messaging**: `assert_jira_mcp_discoverability_guidance` produces structured, actionable failure messages identifying the exact `request.id` and all sorted missing fragments (such as `['50']`), without leaking sensitive information or dumping full fixtures.

## Observability Requirements Analysis

| Area | Finding |
| ---- | ------- |
| Key components | Locked discoverability table `JIRA_MCP_DISCOVERABILITY_SUBSTRINGS` and checker `assert_jira_mcp_discoverability_guidance` in `tests/test_example_fixtures.py`; shipped fixture `examples/collections/jira_mcp.json` and `examples/README.md` |
| Critical paths | None in application runtime code; CI/dev runs load fixtures offline and assert discoverability contracts (positive parametrized tests + single-fragment mutation tests + multi-fragment mutation tests) |
| Performance metrics | Not applicable — no new runtime path or exporter |

When contributors or users import the curated Jira collection and execute requests or expose them as MCP tools, **existing** product observability applies unchanged:
- Request send / error logging on the standard HTTP path
- MCP activity log and UI (tool invocations from `expose_as_mcp` requests)
- Prometheus scrape endpoint for HTTP and MCP usage counters

References (unchanged product docs):
- [examples/README.md](../../examples/README.md) — inventory, import order, secret rules
- [MCP Integration](../../doc/mcp_integration.md) — MCP expose surface
- [Prometheus Monitoring](../../doc/prometheus_monitoring.md) — scrape endpoint
- [Observability audit](../../doc/dev/observability_audit.md) — MCP activity log and metrics overview

## Logging Implementation

### Added Logs

None. No production logging was added to `pypost/`.

- **EMERG**: N/A - no production logging
- **ALERT**: N/A - no production logging
- **CRIT**: N/A - no production logging
- **ERR**: N/A - no production logging
- **WARNING**: N/A - no production logging
- **NOTICE**: N/A - no production logging
- **INFO**: N/A - no production logging
- **DEBUG**: N/A - no production logging

### Test-Time Diagnostic Observability (Test Assertion Messages)

Checker `AssertionError` messages provide deterministic, actionable CI/dev diagnostic signals rather than production syslog streams:

| Checker / Assertion | Diagnostic Message Format | Trigger Scenario |
| ------------------- | ------------------------- | ---------------- |
| `assert_jira_mcp_discoverability_guidance` | `Request {request.id} mcp_description missing locked discoverability fragment(s): {missing}` | Triggered when one or more required lowercase substrings are missing from `request.mcp_description.lower()`. Names `request.id` and lists all missing fragments sorted. |

Diagnostic properties of the assertion message:
- **Identifies Target Request**: Names `request.id` (e.g. `jira-move-issues-to-backlog`) so developers immediately know which MCP tool breached the contract.
- **Lists All Missing Fragments (Sorted)**: Evaluates all required substrings and reports all missing fragments in deterministic sorted order (e.g. `['50']` or `['50', 'membership', 'remove-from-sprint']`), avoiding partial iteration ambiguity.
- **Excludes Present Fragments**: Fragments that are retained in the description are omitted from the missing list, pinpointing exact omissions.
- **No Secret/Large Object Leakage**: Never dumps full JSON fixtures, environment tokens, or raw request payloads.

Mutation tests (`test_jira_mcp_discoverability_rejects_stripped_backlog_membership_guidance` and parametrized `test_jira_mcp_discoverability_rejects_each_single_stripped_fragment`) pin this failure diagnostic format via `pytest.raises(AssertionError, match=...)`.

### Log Structure

Log format used:
- Structured logs: N/A (no production logs)
- Includes context: pytest assertion context only (`request.id`, sorted missing substring list)
- Log levels: none added

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:
- **Response time**: N/A - no runtime change
- **Throughput**: N/A - no runtime change
- **Error rate**: N/A - no runtime change

### Business Metrics

Business metrics:
- N/A - static test fixture contracts and documentation do not emit business metrics

### System Health Metrics

System health metrics:
- **Resource usage**: N/A - CPU, memory, disk uninstrumented for offline tests
- **Component status**: N/A

### Test Suite Execution Signal

The quality and regression signal is deterministic test suite execution:
- Passing tests: 33/33 passing in `tests/test_example_fixtures.py` (~0.08s execution time).
- CI gate: Non-zero exit code on failure when discoverability guidance or batch limit guidance is altered or stripped.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics (N/A — existing product scrape unchanged; no new series)
- [ ] Grafana dashboards (N/A)
- [ ] Alerting rules (N/A)
- [ ] Log aggregation (ELK, Loki, etc.) (N/A)

## Validation Results

Validation results:
- [x] Logs are correctly formatted (N/A — no production logging code; test assertion messages strictly formatted and verified)
- [x] Metrics are collected correctly (N/A — no new production metrics added)
- [x] Logging works in error scenarios (Test failure diagnostics verified via mutation tests with `pytest.raises`)
- [x] Large data structures are not logged (Assertion messages only include `request.id` and missing string fragments; no full collections dumped)
- [x] Metrics are available for monitoring (Unchanged product surface; existing Prometheus / MCP activity log remains available for product runtime)

## Notes

- This deliverable modifies documentation, fixture descriptions, and contract tests (`examples/collections/jira_mcp.json`, `examples/README.md`, `tests/test_example_fixtures.py`). No production code in `pypost/` was modified.
- Test-failure observability is provided via high-clarity `AssertionError` messages that name the offending request ID and the exact sorted list of missing discoverability fragments including `"50"`.
- Step 6 roadmap status is set to `[/]` per workflow guidelines.
