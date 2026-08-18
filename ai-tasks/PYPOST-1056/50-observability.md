# PYPOST-1056: Observability Implementation

## Observability Decision

PYPOST-1056 adds an offline mutation-contract regression test guard (`test_jira_mcp_critical_rest_paths_rejects_url_drift` in `tests/test_example_fixtures.py`) and extends the focused verification target `check-jira-mcp-path-freshness` in `Makefile`.

No runtime application code in `pypost/`, daemon background service, production logging subsystem, or HTTP endpoint handlers were introduced or modified. Consequently, runtime production logging, Prometheus metrics, Grafana dashboards, and live telemetry alerting are not applicable (N/A) to this offline test-only task.

The primary observability surface for this task is the **diagnostic feedback and failure observability** of the offline path freshness validation comparator (`assert_jira_mcp_critical_rest_paths_match_catalog`), ensuring actionable `AssertionError` diagnostics when catalog drift occurs.

---

## Logging Implementation

### Added Logs

No production runtime application logs were added.

- **EMERG**: N/A — no production runtime component or critical system failure path.
- **ALERT**: N/A — no runtime immediate-intervention alerting path.
- **CRIT**: N/A — no production operational runtime path.
- **ERR**: N/A — runtime exception logging unchanged in `pypost/`.
- **WARNING**: N/A — no runtime warning emissions.
- **NOTICE**: N/A — no runtime event notifications.
- **INFO**: N/A — no runtime informational logging.
- **DEBUG**: N/A — no runtime debug logging.

### Log Structure

- **Structured logs**: N/A (no production runtime logging added).
- **Includes context**: Yes — test failure assertions emit structured, context-rich error messages.
- **Log levels**: N/A (standard pytest test execution and assertion output in CI/developer terminals).

---

## Metrics Implementation (if applicable)

### Performance Metrics

- **Response time**: N/A — offline test executes in ~2ms.
- **Throughput**: N/A.
- **Error rate**: N/A.

### Business Metrics

- None added (N/A for fixture/test validation).

### System Health Metrics

- **Resource usage**: N/A — negligible CPU/memory footprint during offline test execution.
- **Component status**: N/A.

---

## Monitoring Integration

- [ ] Prometheus metrics (N/A — offline developer/CI test gate)
- [ ] Grafana dashboards (N/A — no production metric stream)
- [ ] Alerting rules (N/A — CI test failures surface as build pipeline status)
- [ ] Log aggregation (ELK, Loki, etc.) (N/A)

---

## Diagnostic Error Reporting on Drift

The core diagnostic requirement of PYPOST-1056 is verifying that when the curated Jira MCP collection drifts from the locked critical REST path catalog, maintainers receive clear, deterministic, and immediately actionable diagnostics.

### Comparator Diagnostic Contract

In `tests/test_example_fixtures.py`, `assert_jira_mcp_critical_rest_paths_match_catalog` checks every locked catalog entry against the imported collection and raises an `AssertionError` with specific diagnostic details:

| Failure Mode | Raised Diagnostic Format | Pinned in Test |
| :--- | :--- | :--- |
| **Missing Request ID** | `jira_mcp.json missing critical request id {request_id}` | Verified by schema/catalog tests |
| **Method Mismatch** | `{request_id} method drifted: expected {method}, got {request.method}` | Enforced by comparator |
| **Missing Required URL Fragment** | `{request_id} URL missing locked fragment {fragment!r}: {request.url}` | **Explicitly pinned by `test_jira_mcp_critical_rest_paths_rejects_url_drift`** |
| **Unexpected Excluded URL Fragment** | `{request_id} URL unexpectedly contains {fragment!r}: {request.url}` | Enforced by comparator |
| **Missing MCP Parameter** | `{request_id} missing locked mcp_params key {mcp_param!r}` | Enforced by comparator |

### Diagnostic Details Breakdown

When drift is introduced (e.g. mutating `/rest/api/3/search/jql` to `/rest/api/3/search` for `jira-search-issues-jql`), the raised `AssertionError` contains all three critical troubleshooting elements:

1. **Request Identifier**: `jira-search-issues-jql` — Pinpoints the exact MCP tool / request that drifted.
2. **Locked Fragment**: `'/rest/api/3/search/jql'` — Shows the required path component that failed to match.
3. **Observed URL**: `{{jira_base_url}}/rest/api/3/search` — Shows the actual URL found in the collection.

```python
# Example diagnostic message:
"jira-search-issues-jql URL missing locked fragment '/rest/api/3/search/jql': {{jira_base_url}}/rest/api/3/search"
```

### Safety and Confidentiality

- **Zero Credential Exposure**: The diagnostic operates strictly on template URLs (e.g., `{{jira_base_url}}...`) and fixture models. No real credentials, tokens, or live Jira URLs are ever ingested, formatted, or exposed.
- **Offline Determinism**: No external network requests or DNS resolutions are made; the diagnostic is 100% reproducible in isolated CI environments.

---

## Validation Results

- [x] Diagnostic error reporting on drift verified via `test_jira_mcp_critical_rest_paths_rejects_url_drift`
- [x] `AssertionError` explicitly verifies request ID (`jira-search-issues-jql`), locked fragment (`/rest/api/3/search/jql`), and observed URL (`{{jira_base_url}}/rest/api/3/search`)
- [x] Focused verification command passed: `make check-jira-mcp-path-freshness` (2/2 passed in ~0.05s)
- [x] Full fixture suite passed: `tests/test_example_fixtures.py` (32/32 passed in ~0.09s)
- [x] Fast and deterministic: all tests execute with module-level timeout (`pytestmark = pytest.mark.timeout(30)`)
- [x] No sensitive or large data structures emitted to diagnostics
- [x] Code cleanliness and PEP 8 compliance verified via `make lint`

---

## Notes

- The mutation test guard provides long-term regression protection for developer-facing error messages, ensuring that future refactoring of `assert_jira_mcp_critical_rest_paths_match_catalog` cannot accidentally degrade diagnostic clarity or omit essential identifiers.
- Closes technical debt item TD-1 from PYPOST-1030.
