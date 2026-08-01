# PYPOST-940: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: shared `detach_item_view_model` / `close_item_view_fixture`
in `tests/helpers/qt_item_view.py`; tree and list-view ui_select fixtures
use it; ui_select tests pass with no Qt teardown warnings.

## Shortcuts Taken

- **Helper scoped to test tree/list fixtures** — Does not yet wrap
  `collections_tree.py` isolated harnesses; that module owns its own lifecycle.
- **view_type parameter** — Callers pass `QTreeView` / `QListView` for
  isinstance guard; default is `QAbstractItemView`.

## Code Quality Issues

None blocking. Helper is small and mirrors the prior inline pattern.

## Missing Tests

| Scenario | Status |
| --- | --- |
| detach_item_view_model clears model | Covered (`test_qt_item_view_teardown.py`) |
| close_item_view_fixture tree path | Covered |
| ui_select tree/list fixtures use helper | Covered (integration via `test_ui_actions.py`) |
| collections_tree harness teardown | Not in scope — separate fixture module |

## Performance Concerns

None.

## Deviations from Architecture

None.

## Follow-up Tasks

### NON-BLOCKER

| ID | Priority | Item | Notes |
| --- | --- | --- | --- |
| TD-1 | Low | Adopt qt_item_view teardown in collections_tree if isolated views grow | Only if duplicate setModel(None) appears there |

### Already tracked elsewhere (do not reticket)

| Area | Owner |
| --- | --- |
| Source PYPOST-916 TD-2 | This story (PYPOST-940) |
| DisplayRole scan sharing | [PYPOST-941](https://pypost.atlassian.net/browse/PYPOST-941) |
| Out-of-range list/tree tests | [PYPOST-942](https://pypost.atlassian.net/browse/PYPOST-942) |

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None |
| Missing tests with timeout markers | **None** |
| Deviations from architecture | None |
| Acceptance gaps | **None** |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE**
