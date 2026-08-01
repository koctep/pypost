# PYPOST-939: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: documented `ui_select` API for `QListView` / flat
`QAbstractItemView`; tests cover non-`QListWidget` / non-`QTreeView` paths;
combo, list widget, and tree behaviour unchanged.

## Shortcuts Taken

- **Flat column 0 only** — Model-backed views scan DisplayRole on column 0;
  sufficient for `QListView` golden flows; table/multi-column deferred.
- **Linear text scan** — O(rows) per select; fine for harness-sized lists.
- **Reuse dispatch, not `_select_list`** — `QListWidget` keeps widget-item API.

## Code Quality Issues

- `_select_item_view` and `_select_tree` share DisplayRole matching patterns;
  optional consolidation if more model views land (TD-1).

## Missing Tests

| Scenario | Status |
| --- | --- |
| `QListView` by text / index | Covered |
| `QListWidget` / tree / combo regression | Covered (fixture subset) |
| Item view missing model | Not dedicated (TD-2) |
| Out-of-range index on item view | Not dedicated (inherits PYPOST-942 scope) |
| Live product `QListView` via agent_e2e | N/A — no product list view id today |

## Performance Concerns

None for harness use.

## Deviations from Architecture

None material.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| List/tree out-of-range tests | [PYPOST-942](https://pypost.atlassian.net/browse/PYPOST-942) |
| Fixture teardown helper | [PYPOST-940](https://pypost.atlassian.net/browse/PYPOST-940) |
| Tree text walk sharing | [PYPOST-941](https://pypost.atlassian.net/browse/PYPOST-941) |

### NON-BLOCKER

| ID | Priority | Item | Notes |
| --- | --- | --- | --- |
| TD-1 | Low | Share flat DisplayRole scan between item view and tree helpers | Only if drift grows. [PYPOST-971](https://pypost.atlassian.net/browse/PYPOST-971) |
| TD-2 | Low | Dedicated `item view has no model` test | Mirror tree no-model coverage. [PYPOST-972](https://pypost.atlassian.net/browse/PYPOST-972) |

### Accepted / out of scope (do not ticket)

- `QTableView` row/column select semantics.
- Product UI migration to plain `QListView`.

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None |
| Missing tests with timeout markers | **None** — module `timeout(60)` |
| Deviations from architecture | None |
| Acceptance gaps | **None** |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE**
