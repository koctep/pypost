# PYPOST-942: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: four dedicated list/tree negative-path contract tests in
`tests/test_ui_actions.py` mirror `test_select_missing_option_raises`; module
green (27 passed); closes [PYPOST-916/60-tech-debt.md](../PYPOST-916/60-tech-debt.md)
TD-4. No production code changed.

## Shortcuts Taken

- **Green-on-first-run contract tests** — Error paths already exist in
  `_select_list` / `_select_tree`; Step 3 skipped deliberate red-before-green
  (coverage debt only).
- **Substring assertions** — Tests assert `"option not found"` /
  `"option index out of range"` in `str(exc_info.value)`, matching combo
  precedent; avoids brittle full-string matching on `widget_id` formatting.
- **Parametrized index boundaries** — One test per widget type covers `-1` and
  `count` (list: 3, tree top-level: 2) instead of four separate functions.

## Code Quality Issues

None material. New tests reuse `_make_fixture` / `_make_tree_fixture`, inherit
module `pytestmark`, and follow established `try`/`finally` teardown.

## Missing Tests

| Scenario | Status |
| --- | --- |
| List missing display text | Covered (`test_select_list_missing_option_raises`) |
| List index `< 0` / `>= count` | Covered (parametrized `-1`, `3`) |
| Tree missing display text | Covered (`test_select_tree_missing_option_raises`) |
| Tree top-level index `< 0` / `>= rowCount` | Covered (parametrized `-1`, `2`) |
| Combo missing option (regression) | Covered (pre-existing) |
| Combo out-of-range index | Not covered — separate gap (see follow-ups) |
| Nested tree index out-of-range | Out of scope — top-level index contract (PYPOST-916) |
| `QListView` negative paths | Out of scope — [PYPOST-939](https://pypost.atlassian.net/browse/PYPOST-939) |
| Live `COLLECTION_TREE` via `agent_e2e_session` | Deferred — fixture suite proves API |
| Explicit timeout markers | **Present** — module `pytest.mark.timeout(60)` |

## Performance Concerns

None. Negative-path tests are synchronous fixture calls with no event-loop
polling.

## Deviations from Architecture

None. Test-only change delivered as planned in `20-architecture.md`; production
module graph unchanged.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Parent TD-4 (list/tree negative tests) | This story (PYPOST-942) |
| `QListView` / generic item-view select | [PYPOST-939](https://pypost.atlassian.net/browse/PYPOST-939) |
| Qt item-view fixture teardown helper | [PYPOST-940](https://pypost.atlassian.net/browse/PYPOST-940) |
| Shared tree DisplayRole walk | [PYPOST-941](https://pypost.atlassian.net/browse/PYPOST-941) |

### NON-BLOCKER

| ID | Priority | Item | Notes |
| --- | --- | --- | --- |
| TD-1 | Low | Combo out-of-range index contract test | `_select_combo` raises the same `option index out of range` string; only missing-option is tested today. Mirror parametrized list/tree pattern. Jira: [PYPOST-974](https://pypost.atlassian.net/browse/PYPOST-974) |
| TD-2 | Low | Live collection-tree negative select via `agent_e2e_session` | Optional hardening; fixture tests lock the agent API. Jira: [PYPOST-975](https://pypost.atlassian.net/browse/PYPOST-975) |

### Accepted / out of scope (do not ticket)

- Tree missing-text overlap with `tests/test_tree_index_walk.py` — different
  fixture contract; fixture-suite parity was the TD-4 acceptance target.
- Assert full `reason=` / `widget_id=` on every negative test — combo reference
  test uses substring only; consistent across select types.

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None |
| Missing tests with timeout markers | **None** |
| Deviations from architecture | None |
| Acceptance gaps | **None** — FR1–FR6 satisfied |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — list/tree negative select errors are locked by dedicated
fixture tests; remaining gaps are optional parity hardening.
