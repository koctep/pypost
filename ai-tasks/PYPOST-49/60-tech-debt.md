# PYPOST-49: Technical Debt Analysis

## Review Summary

**Verdict:** SAFE TO CLOSE. Audit R7 is satisfied: `MetricsRegistry` owns counters,
`MetricsServer` owns uvicorn/MCP, and `MetricsManager` remains a thin facade. Metric names,
labels, routes, and injection API are unchanged. All focused unit tests pass.

| Requirement | Status | Evidence |
| --- | --- | --- |
| Registry owns counters (no I/O) | Met | `pypost/core/metrics_registry.py` |
| Server owns uvicorn + MCP | Met | `pypost/core/metrics_server.py` |
| Facade preserves injection API | Met | `pypost/core/metrics.py` |
| Tests pass | Met | 25/25 in metrics test modules |
| No telemetry behavior change | Met | Existing test assertions unchanged |

## Shortcuts Taken

- **`MetricsManager` facade retained** instead of updating 20+ injection sites to
  `MetricsRegistry` / `MetricsServer` separately. Reduces blast radius; acceptable trade-off
  documented in PYPOST-75.

## Code Quality Issues

- None blocking. `doc/dev/architecture.md` previously described `MetricsManager` as a singleton;
  corrected in Step 7.

## Missing Tests

- Live metrics-server MCP SSE round-trip remains out of scope (pre-existing debt tracked in
  PYPOST-370 / PYPOST-177). Not a blocker for R7 closure.

## Performance Concerns

- None. Structural refactor only; no runtime path changes.

## Follow-up Tasks

| Priority | Description | Jira |
| --- | --- | --- |
| Low | Introduce `MetricsProtocol` + `NullMetrics` (PYPOST-44 TD-2) | Out of R7 scope; track under injection cleanup |
| Low | Composition root could inject `MetricsServer` separately when only startup needs server API | Deferred |

No new Jira tickets required to close PYPOST-49. Follow-ups above are optional enhancements
outside audit R7 acceptance criteria.
