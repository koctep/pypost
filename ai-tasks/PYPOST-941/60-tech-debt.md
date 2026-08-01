# PYPOST-941: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: one shared DisplayRole tree walk in
`pypost/agent/tree_index.py`; `ui_select` and `agent_e2e_tree` delegate;
`AssertionError` vs `UiTargetNotInteractableError` preserved; tests green.

## Shortcuts Taken

- **Production module for shared walk** — e2e helper imports from
  `pypost.agent.tree_index` (tests already depend on agent package).
- **Return `None` on miss** — callers map to assertion vs agent errors.

## Code Quality Issues

None material. Duplication removed; e2e helper now supports arbitrary depth.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Deep (3-level) e2e helper find | Covered (`test_tree_index_walk.py`) |
| Shared walk miss → `None` | Covered |
| E2e `AssertionError` vs agent error | Covered |
| ui_select tree regression | Covered via `test_ui_actions.py` |
| Agent e2e click_tree_row_by_text | Covered via seed/http seed tests |

## Performance Concerns

None. Same O(nodes) depth-first walk as before.

## Deviations from Architecture

None.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Flat list DisplayRole scan sharing | [PYPOST-939](../PYPOST-939/60-tech-debt.md) TD-1 |
| Out-of-range list/tree tests | [PYPOST-942](https://pypost.atlassian.net/browse/PYPOST-942) |

### NON-BLOCKER

None — TD-3 from PYPOST-916 is resolved by this task.

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None |
| Missing tests with timeout markers | **None** — module `timeout(30)` |
| Deviations from architecture | None |
| Acceptance gaps | **None** |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE**
