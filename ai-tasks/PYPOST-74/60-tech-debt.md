# PYPOST-74: Review and technical debt

## Verdict

**SAFE TO CLOSE** — NullMetrics implemented, guards removed, targeted tests pass.

## Resolved debt

| Item | Resolution |
| --- | --- |
| PYPOST-44 TD-2 repeated `if self._metrics` guards | `NullMetrics` + `resolve_metrics` |

## Follow-ups

| Priority | Jira | Item |
| --- | --- | --- |
| Low | [PYPOST-75](https://pypost.atlassian.net/browse/PYPOST-75) | Duplicate scope (NullMetrics) — close or narrow to counter split only |
| Low | [PYPOST-675](https://pypost.atlassian.net/browse/PYPOST-675) | Gradually type consumer params as `MetricsTrackerProtocol` without `\| None` |

## Notes

- `collection_tree_actions.py` already called metrics unconditionally when MainWindow injects
  real tracker — unchanged.
- Composition root (`main.py`, `MainWindow`) still owns `MetricsManager` lifecycle.
