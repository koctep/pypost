# PYPOST-972: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: dedicated `test_select_list_view_no_model_raises` locks
`UiTargetNotInteractableError` with `"item view has no model"` for a
model-less `QListView`; module green (33 passed); closes
[PYPOST-939/60-tech-debt.md](../PYPOST-939/60-tech-debt.md) TD-2. No production
code changed.

## Shortcuts Taken

- **Green-on-first-run contract test** — Error path already exists in
  `_select_item_view`; classic red-before-green N/A (coverage debt only).
- **Substring assertions** — Asserts `"item view has no model"` in
  `str(exc_info.value)` and that `"tree has no model"` is absent (FR-4),
  matching PYPOST-942 / combo negative-path style.
- **No-model-from-start fixture** — Isolated `QListView` without `setModel`
  rather than reusing the happy-path model helper then detaching.

## Code Quality Issues

None material. New test reuses `_LIST_VIEW`, inherits module `pytestmark`, and
follows established `try`/`finally` + `close_item_view_fixture` teardown.

## Missing Tests

| Scenario | Status |
| --- | --- |
| `QListView` missing model | Covered (`test_select_list_view_no_model_raises`) |
| `QListView` by text / index | Covered (pre-existing PYPOST-939) |
| List/tree missing option / OOR | Covered (PYPOST-942) |
| Tree missing model | **Not covered** — production raises `"tree has no model"`;
  no dedicated suite assertion (see TD-1) |
| Live product `QListView` e2e | N/A — no product list-view id |
| Explicit timeout markers | **Present** — module `pytest.mark.timeout(60)` |

## Performance Concerns

None. Error-path test is a synchronous fixture call with no event-loop
polling.

## Deviations from Architecture

None. Test-only change delivered as planned in `20-architecture.md`; production
module graph unchanged.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Parent TD-2 (item-view no-model test) | This story (PYPOST-972) |
| List/tree missing option / OOR | [PYPOST-942](https://pypost.atlassian.net/browse/PYPOST-942) |
| Shared DisplayRole scan | [PYPOST-971](https://pypost.atlassian.net/browse/PYPOST-971) |

### NON-BLOCKER

| ID | Priority | Item | Notes |
| --- | --- | --- | --- |
| TD-1 | Low | Dedicated `tree has no model` contract test | Mirror
  `test_select_list_view_no_model_raises` for `_select_tree` when
  `model()` is `None`. Out of scope for PYPOST-972 (“mirror tree” meant
  same failure family + distinct reason string).
  **Jira:** [PYPOST-1042](https://pypost.atlassian.net/browse/PYPOST-1042) |

### Accepted / out of scope (do not ticket)

- Live product `QListView` agent e2e — no product list-view id today.
- Changing missing-model error wording — locked public contract.
- Expanding to missing-option / OOR for item views — owned elsewhere.

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None |
| Missing tests with timeout markers | **None** |
| Deviations from architecture | None |
| Acceptance gaps | **None** — FR-1–FR-6 / AC-1–AC-6 satisfied |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — item-view missing-model contract is locked by a dedicated
fixture test; tree no-model automated coverage remains optional follow-up.
