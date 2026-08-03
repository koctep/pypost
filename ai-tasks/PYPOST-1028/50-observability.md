# PYPOST-1028: Observability Implementation

## Verdict

**N/A for production logging and metrics — offline fixture-contract tests
only.** This story hardens agreements in `tests/test_example_fixtures.py`
(companion env coverage, Basic auth convention, `mcp.request.*` ↔
`mcp_params`, fixed-input allowlist freeze, agent-driven query/body). No
application packages under `pypost/`, request send paths, MCP handlers,
logging calls, or Prometheus instruments were added or changed.

Observability for this deliverable is limited to **pytest assertion
diagnostics**: failure messages name the breached agreement (request id,
missing companion key, missing `mcp_params` name, allowlist drift) without
logging secrets, full fixtures, or large structures.

## Observability Requirements Analysis

| Area | Finding |
| ---- | ------- |
| Key components | Shared checkers and allowlist in
  `tests/test_example_fixtures.py`; shipped fixtures remain read-only inputs |
| Critical paths | None in application code; CI/dev runs load fixtures offline and
  assert the four contracts (positive + mutation negatives) |
| Performance metrics | Not applicable — no new runtime path or exporter |

When contributors later import the curated collection and run requests (or
expose them as MCP tools), **existing** product observability applies
unchanged. This story does not add series, log lines, or dashboards.

References (unchanged product docs):

- [examples/README.md](../../examples/README.md) — inventory, import order,
  secret rules
- [MCP Integration](../../doc/mcp_integration.md) — MCP expose surface
- [Prometheus Monitoring](../../doc/prometheus_monitoring.md) — scrape
  endpoint
- [Observability audit](../../doc/dev/observability_audit.md) — MCP activity
  log and metrics overview

## Logging Implementation

### Added Logs

None. No production logging was added.

- **EMERG / ALERT / CRIT / ERR / WARNING / NOTICE / INFO / DEBUG**: N/A

### Test-time diagnostics (not syslog)

Checker `AssertionError` messages are the actionable CI signal. They are
not application logs and are not routed to log aggregation:

| Checker | Diagnostic signal |
| ------- | ----------------- |
| `assert_jira_mcp_companion_env_coverage` | `Missing companion key(s): [...]`
  (sorted missing env names) |
| `assert_jira_mcp_auth_convention` | `Request {id} auth convention breach`
  (expected Basic `base64(jira_credentials)`; no header value dumped) |
| `assert_jira_mcp_params_declared` | `Request {id} missing mcp_params
  key(s): [...]` |
| `assert_jira_mcp_fixed_input_allowlist` | empty-`mcp_params` id set vs
  `FIXED_INPUT_JIRA_MCP_REQUEST_IDS` (both sides sorted) |
| `assert_jira_mcp_agent_driven_declares_inputs` | `Request {id} is
  agent-driven without mcp_params and outside
  FIXED_INPUT_JIRA_MCP_REQUEST_IDS` |

Mutation tests pin these signals with `pytest.raises(..., match=...)` so
diagnostics stay named and regression-safe.

### Log Structure

- Structured logs: N/A (no runtime logs)
- Includes context: pytest assertion context only (request id, key names,
  allowlist set membership)
- Log levels: none added
- Large/sensitive data: messages never include credential values, full
  request bodies, header maps, or entire collection/environment dumps

## Metrics Implementation (if applicable)

### Performance Metrics

N/A — no runtime change. No fake metrics for fixture import rates, contract
pass rates, or per-request counters in the curated collection.

### Business Metrics

N/A — curated fixture agreements are repository quality gates, not business
events.

### System Health Metrics

N/A.

### Deterministic contract signal

The focused pytest result is the quality measurement: positive tests on
shipped fixtures plus mutation negatives that prove each checker fails with
the expected diagnostic. Non-zero exit from
`make test PYTEST_ARGS='tests/test_example_fixtures.py'` is the CI signal,
not a Prometheus series.

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics — N/A (product scrape unchanged; no new series)
- [ ] Grafana dashboards — N/A
- [ ] Alerting rules — N/A
- [ ] Log aggregation (ELK, Loki, etc.) — N/A

## Validation Results

Validation results:

- [x] No new application logs required for test-only deliverable
- [x] No new metrics invented or documented as if newly implemented
- [x] Checker failure messages name request id / missing key / allowlist
  drift; mutation tests assert those patterns
- [x] Large data structures and secrets are not logged — N/A for production
  logs; assertion messages omit credentials and full fixtures
- [x] Metrics available for monitoring — unchanged product surface; not
  part of this deliverable
- [x] Contract tests in `tests/test_example_fixtures.py` are CI/dev checks
  only — not production metrics or log sources

## Notes

Step 6 documents an explicit runtime N/A with limited test-time diagnostic
coverage. Adding OTel spans, syslog lines, or Prometheus counters for
offline fixture-contract helpers would invent signals operators cannot
scrape or act on. Fixture drift remains visible through deterministic
pytest failures before merge. Runtime visibility for imported Jira MCP
tools remains the existing MCP activity log and Prometheus HTTP/MCP
instruments already documented for the product.

Roadmap Step 6 left as `[/]` pending review.
