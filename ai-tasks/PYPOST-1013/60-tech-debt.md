# PYPOST-1013: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE — DoD met. Context-menu **Export Collection…** shares
orchestration with the below-tree button via optional `source_index`. No blockers.
Remaining items are soft coverage and pre-existing CI hygiene.

Scope reviewed: `collection_export_actions.py`, `collection_tree_actions.py`,
`collections_presenter.py`, `tests/helpers/collections_tree.py`,
`tests/test_collection_tree_actions.py` (+ helper call-site bumps), user/dev docs
touched in development, and `ai-tasks/PYPOST-1013/*`.

## Shortcuts Taken

- **Optional export callback on tree actions** — `export_collection` defaults to
  `None` so isolated rename/delete harnesses can omit it; production
  `CollectionsPresenter` always injects `_export_collection_at_index`. Same DI
  style as other emits, with a soft-opt-out for tests.
- **No new Prometheus / GUI metrics** — menu path logs
  `collection_export_selected`; outcomes reuse PYPOST-989 `collection_export_*`
  events. Matches architecture Q&A and Step 6.
- **Positional mock action lists** — rename/delete suites still build
  `[Export?, …, Rename, Delete]` by `action_count` rather than label lookup.
  Fragile if menu order changes again; documented in helpers after the bump
  (3 collection / 4 request).
- **Docs updated during development** — `doc/user/collections.md`,
  `doc/dev/collection_export.md`, and `doc/dev/collection_tree_actions.md`
  already describe the menu path. Step 8 may only need a final consistency pass
  (catalog / logging index if still incomplete).

## Code Quality Issues

- **Thin presenter shim** — `_export_collection_at_index` is a one-liner to
  `CollectionExportActions.export_collection(source_index=…)`. Clear and typed;
  not worth collapsing unless more entry points appear.
- **Local callback bind for mypy** — `show_context_menu` copies
  `self._export_collection` to a local before call to satisfy `"None" not
  callable`. Correct and small; no further cleanup needed.
- **Hardcoded menu order** — Export sits between optional **New tab** and
  **Rename**. Intentional discoverability grouping; tests lock the order.

No material hardcoded magic values beyond existing
`BUTTON_EXPORT_COLLECTION` / structured log event names.

## Missing Tests

**No blocker.** Touched suites use module `pytestmark = pytest.mark.timeout(60)`
(or equivalent) per `.cursor/lsr/do-testing.md`.

| Scenario | Status |
| -------- | ------ |
| Collection menu includes Export Collection… | Present |
| Request menu includes Export (parent collection semantics via index) | Present |
| Menu dispatch passes **clicked** index to export callback | Present |
| Menu logs `collection_export_selected` | Present |
| Button path still uses `currentIndex()` / no-arg export | Present (PYPOST-989 UI suite) |
| Explicit pytest timeout markers | Present — not a blocker |
| **`source_index` overrides a distant `currentIndex()`** through
  `CollectionExportActions` (save/write target = clicked collection, not
  selection) | **Missing** (soft gap) |
| Presenter wiring assertion that tree callback is
  `_export_collection_at_index` | Missing (low value; covered by construction) |
| Full GUI mouse right-click → real `QMenu` → file write | Missing (out of
  pattern; mocked `QMenu` is project norm) |

## Performance Concerns

None. Export remains a rare, synchronous, user-initiated action; menu path adds
one INFO log and the same dialog/write work as the button.

## Deviations from Initial Architecture

None material. Delivery matches `20-architecture.md`:

- Optional `source_index` on `CollectionExportActions.export_collection`
- Tree menu offers Export on collection and request rows
- Presenter injects clicked-index callback; button keeps no-arg `currentIndex()`
- Shared core + dialogs; no format change
- Observability: selection event + reused outcome logs

## Follow-up Tasks

Do **not** create Jira issues in this Step 7 run (orchestrator Phase D).

1. **Integration / unit test: `source_index` beats distant `currentIndex`** —
   Build a tree with two collections, set `currentIndex` to collection A, call
   `export_collection(source_index=B)` (or menu path with B clicked) and assert
   save/serialize targets B. Closes the soft gap left by dispatch-only mocks.
   - Priority: Medium
   - Jira: [PYPOST-1064](https://pypost.atlassian.net/browse/PYPOST-1064)

2. **mypy baseline line-number drift** — Step 5 noted count churn (e.g. 219 vs
   218) from line-keyed baseline entries outside this task’s real errors. Already
   ticketed; do not recreate.
   - Priority: Low
   - Jira: [PYPOST-1007](https://pypost.atlassian.net/browse/PYPOST-1007)

### Accepted / out of scope (do not ticket from this story)

- Shared JSON write helper (PYPOST-1011), export-all (PYPOST-1012) — prior debt.
- Removing the below-tree Export button or sidebar layout redesign.
- Adding Prometheus counters for export entry points.
- Replacing positional `action_count` menu mocks with label-based selection
  (project-wide helper pattern; only worth a sweep if menus keep growing).

## User documentation

User guide already covers right-click **Export Collection…** alongside the
button (`doc/user/collections.md`). No further user-doc debt for this step.
Dev-doc polish, if any, belongs in Step 8.

## Blocker Review

| Check | Result |
| ----- | ------ |
| Temporary solutions / crutches | Soft only; none block close |
| Missing tests with timeout markers | **None** — markers present |
| Hardcoded values | None material |
| Deviations from architecture | None material |
| Acceptance gaps vs DoD | None |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** for PYPOST-1013 Step 7; follow-ups are coverage polish and
existing CI baseline hygiene, not incomplete feature work.
