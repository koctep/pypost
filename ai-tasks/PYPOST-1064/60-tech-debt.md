# PYPOST-1064: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE — Definition of Done fully satisfied. The gap from PYPOST-1013 (verifying that `source_index` overrides distant `currentIndex` during collection export) is thoroughly tested and verified. All tests pass with explicit timeout markers, static analysis has 0 warnings/errors, and mypy baseline is preserved.

Scope reviewed:
- `pypost/ui/presenters/collections_presenter.py`
- `pypost/ui/presenters/collection_export_actions.py`
- `tests/test_collection_export_ui.py`
- `ai-tasks/PYPOST-1064/*`

---

## Shortcuts Taken

- **Qt Dialog Mocking:** Standard test mocking for `prompt_export_collection_file` and `show_collection_export_result` is used instead of real GUI file picker popups. This is the established pattern across UI test suites in the codebase to allow deterministic, headless test execution in CI.
- **Linear Model Traversal in Test Helpers:** `_index_for_collection` and `_index_for_request` use linear row iteration over the `QStandardItemModel`. For test tree fixtures containing a handful of items, this runs in <1ms and keeps test setup clear and deterministic without extra indexing overhead.

---

## Code Quality Issues

- **Test Helper Location:** Helper functions `_index_for_collection` and `_index_for_request` are currently located within `tests/test_collection_export_ui.py`. If future tree action tests (e.g. import, duplicate, move) require finding `QModelIndex` by collection or request ID, these helpers could be factored into `tests/helpers/collections_tree.py`.
- **Presenter Signature Alignment:** `CollectionsPresenter.export_collection` was updated to accept `source_index: QModelIndex | None = None` matching `CollectionExportActions.export_collection(source_index=source_index)`. This maintains uniform parameter forwarding.

---

## Missing Tests

**No blockers.** All tests declare `pytestmark = pytest.mark.timeout(60)` per testing standards.

| Scenario | Status |
| -------- | ------ |
| `source_index` on Collection B with `currentIndex()` on Collection A exports Collection B | **Covered** (`test_source_index_pointing_to_collection_overrides_distant_current_index`) |
| `source_index` on Request B with `currentIndex()` on Collection A exports parent Collection B | **Covered** (`test_source_index_pointing_to_child_request_exports_its_parent_collection`) |
| `source_index=None` fallback defaults to active `currentIndex()` (Collection A) | **Covered** (`test_export_without_source_index_defaults_to_current_index`) |
| Presenter method `_export_collection_at_index` forwards `source_index` | **Covered** (`test_presenter_export_collection_at_index_forwards_source_index`) |
| Arbitrary deep nested folder structures | N/A — Current data model is 2-level (Collection -> Request). If sub-folders are introduced in the future, recursive parent traversal tests will be added. |

---

## Performance Concerns

None. 
- All 19 tests in `tests/test_collection_export_ui.py` execute in ~0.09s total (each new test takes ~1ms).
- Production target resolution in `_selected_collection_id` operates in O(1) attribute and parent item access, introducing zero measurable latency to collection export.

---

## Follow-up Tasks

No immediate Jira tickets are required for release or merge. Potential future maintenance items:

1. **Shared Tree Index Test Helpers:** If other tree interaction test suites require index lookup by collection ID or request ID, move `_index_for_collection` and `_index_for_request` from `tests/test_collection_export_ui.py` to `tests/helpers/collections_tree.py`.
   - *Priority:* Low
   - *Type:* Refactoring / Test hygiene

2. **Recursive Parent Resolution for Multi-Level Groups (Future Feature):** If nested subfolders or request folders are added to the collections model in the future, enhance `_selected_collection_id` to recursively traverse `parent()` until the root collection item is reached.
   - *Priority:* Low (conditional on future hierarchy feature)
   - *Type:* Feature extension

---

## Blocker Review

| Check | Result |
| ----- | ------ |
| Temporary solutions / crutches | None |
| Missing tests with timeout markers | None — `pytestmark = pytest.mark.timeout(60)` present |
| Code quality / linter warnings | 0 warnings (`flake8` passed) |
| Type check regressions | 0 regressions (`check_mypy_baseline.py` passed) |
| Deviations from architecture | None |
| Acceptance gaps vs DoD | None — all DoD items verified |
