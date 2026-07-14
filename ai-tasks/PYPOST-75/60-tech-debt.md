# PYPOST-75: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE — PYPOST-44 TD-3 addressed; PYPOST-44 TD-2 closed via PYPOST-799; behavior unchanged; tests pass.

## Shortcuts Taken

- **`MetricsManager` facade retained** instead of updating 20+ injection sites to
  `MetricsRegistry` / `MetricsServer`. Reduces blast radius; facade is thin delegation.

## Known Limitations

| Item | Severity | Notes |
| --- | --- | --- |
| Facade still bundles registry + server at type level | Low | Call sites that only need counters still receive full facade | [PYPOST-676](https://pypost.atlassian.net/browse/PYPOST-676) |
| No live uvicorn integration test | Low | Pre-existing; unit tests cover registry scrape and MCP handler |

## Resolved Debt

| Source | Item | Resolution |
| --- | --- | --- |
| PYPOST-44 TD-3 | MetricsManager bundles counters, MCP, uvicorn | Split into `MetricsRegistry` + `MetricsServer` |
| PYPOST-40 / PYPOST-49 | Split MetricsManager | Implemented (facade pattern) |
| PYPOST-44 TD-2 | Optional `MetricsProtocol` / `NullMetrics` / `None` guards at call sites | Closed by [PYPOST-799](https://pypost.atlassian.net/browse/PYPOST-799) — `MetricsTrackerProtocol`, `NullMetrics`, `resolve_metrics()` verified |

## Follow-up Tasks

| Priority | Jira | Description |
| --- | --- | --- |
| Low | [PYPOST-677](https://pypost.atlassian.net/browse/PYPOST-677) | Composition root could inject `MetricsServer` separately when only startup needs server API |

No new Jira tickets required for PYPOST-75 scope.
