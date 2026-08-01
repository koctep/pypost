# PYPOST-916: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: documented `ui_select` API for list/tree by display text or
index; tests cover non-combo list and tree paths; combo-by-text call sites
unchanged. No production UI changes.

## Shortcuts Taken

- **Extend `ui_select` instead of a sibling** — Matches debt wording and
  keeps one agent primitive; session helper updated in place.
- **Tree index = top-level row only** — Nested rows selected by text.
  Clearer contract than opaque flat indices.
- **Selection ≠ open** — Did not replace `click_tree_row_by_text`; product
  open/activate still uses viewport click where needed.
- **No `QListView` / generic `QAbstractItemView` path** — Product agents
  need `QListWidget` + `QTreeView` today; generic view deferred (TD-1).

## Code Quality Issues

- Tree DisplayRole walk is recursive depth-first (similar to e2e helper).
  Fine for collection trees; could share a private helper with
  `tests/helpers/agent_e2e_tree.py` later if drift appears (TD-3).
- Wrong-type error string changed from `not a combo box` to
  `not a selectable list/combo/tree` — intentional; update any external
  string matchers if present (none in-repo beyond docs).

## Missing Tests

| Scenario | Status |
| --- | --- |
| List select by text / index | Covered |
| Tree select by text / top-level index | Covered |
| Combo select by index | Covered |
| Combo select by text (regression) | Covered |
| Out-of-range index / missing list option | Combo missing option covered; list/tree out-of-range not dedicated (TD-4) |
| Live `COLLECTION_TREE` via `agent_e2e_session` | Deferred — fixture proves API; seed still uses click helper for open |
| Explicit timeout markers | **Present** — module `timeout(60)` |

## Performance Concerns

None. Tree walk is O(nodes) per select; suitable for harness use.

## Deviations from Architecture

None material. Delivered extend-`ui_select` + `str | int` + list/tree
dispatch as planned. Optional live collection-tree agent_e2e proof left as
NON-BLOCKER follow-up.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| This story | PYPOST-916 (closing) |
| Source Low debt | [PYPOST-851](https://pypost.atlassian.net/browse/PYPOST-851) TD-1 |

### NON-BLOCKER

| ID | Priority | Item | Notes | Jira |
| --- | --- | --- | --- | --- |
| TD-1 | Low | Support `QListView` / generic `QAbstractItemView` in `ui_select` | Only if a golden flow names a non-widget-item view. | Jira: [PYPOST-939](https://pypost.atlassian.net/browse/PYPOST-939) |
| TD-2 | Low | Harden fixture teardown for Qt item views | Documented `setModel(None)` pattern; consider shared test helper if more tree fixtures appear. | Jira: [PYPOST-940](https://pypost.atlassian.net/browse/PYPOST-940) |
| TD-3 | Low | Share tree text walk with `agent_e2e_tree` | Avoid duplication if both keep growing; keep AssertionError vs agent errors distinct. | Jira: [PYPOST-941](https://pypost.atlassian.net/browse/PYPOST-941) |
| TD-4 | Low | Dedicated out-of-range / missing-option tests for list and tree | Mirror combo `option not found` coverage. | Jira: [PYPOST-942](https://pypost.atlassian.net/browse/PYPOST-942) |

### Accepted / out of scope (do not ticket)

- Replace seed/golden viewport click with `ui_select` for open-request —
  product click still required for activate.
- MCP packaging of UI actions — prior PYPOST-836 debt.

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None relative to acceptance |
| Missing tests with timeout markers | **None** |
| Deviations from architecture | None |
| Acceptance gaps | **None** — docs + non-combo tests shipped |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — broader select is implemented, documented, and locked by
fixture tests; remaining items are optional hardening.
