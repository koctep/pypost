# PYPOST-73: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE — PYPOST-44 TD-1 addressed; behavior unchanged; tests pass.

## Shortcuts Taken

- **`None`-guard pattern retained** at call sites — `NullMetrics` deferred to PYPOST-75 follow-up.

## Known Limitations

| Item | Severity | Notes |
| --- | --- | --- |
| `None` guards still verbose | Low | PYPOST-44 TD-2 — needs `NullMetrics` |
| Facade still bundles server + counters at root | Low | Addressed by PYPOST-75 split; root still uses facade |
| No OpenTelemetry adapter | Low | Future work once protocol exists |

## Resolved Debt

| Source | Item | Resolution |
| --- | --- | --- |
| PYPOST-44 TD-1 | No protocol for metrics consumers | `MetricsTrackerProtocol` + consumer type hints |

## Follow-up Tasks

| Priority | Jira | Description |
| --- | --- | --- |
| Low | [PYPOST-75](https://pypost.atlassian.net/browse/PYPOST-75) | `NullMetrics` no-op to replace `if self._metrics` guards (TD-2) — already tracked |
| Low | [PYPOST-579](https://pypost.atlassian.net/browse/PYPOST-579) | OpenTelemetry adapter implementing `MetricsTrackerProtocol` |

No new Jira tickets required for PYPOST-73 scope beyond existing TD-2 tracker.
