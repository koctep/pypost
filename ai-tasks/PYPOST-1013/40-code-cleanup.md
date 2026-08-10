# PYPOST-1013: Code Cleanup Report

## Linter Fixes

Describe fixed linter errors and warnings:
- Fixed: `export_collection(source_index)` lacked a type hint — annotated as
  `QModelIndex | None` (Step 4 polish)
- Fixed: `_selected_collection_id` index parameter typed as `QModelIndex`
- Fixed: `CollectionsPresenter._export_collection_at_index` typed as
  `QModelIndex`
- Fixed: `CollectionTreeActions.export_collection` callback typed as
  `Callable[[QModelIndex], None] | None` (was `Callable[..., None]`)
- Fixed: mypy `"None" not callable` on export dispatch — bind callback to a
  local and re-check before call
- Fixed: mypy `Qt.UserRole` attr-defined in `collection_export_actions.py` —
  use `Qt.ItemDataRole.UserRole` (same pattern as other typed UI code)
- Fixed: unsorted `pypost.core.*` imports in `collection_tree_actions.py`

## Code Formatting

Applied formatting changes:
- [x] Automatic code formatting — flake8 (`make lint`) clean on `pypost/`
- [x] Indentation and alignment fixes — PEP 8 blank line before test class
- [x] Line length correction — no new >100-char lines in touched sources

## Code Cleanup

Cleanup actions performed:
- Removed unused imports: 0
- Removed unused variables: 0
- Removed commented-out code: none
- Removed debug prints: none
- Removed duplicate menu-composition tests that repeated the same label
  assertions as the Step 3 export-menu tests
  (`test_collection_menu_offers_rename_and_delete`,
  `test_request_menu_offers_new_tab_rename_delete`)

## Validation Results

Validation results:
- [x] All tests passed — focused suite 67 passed
  (`test_collection_tree_actions`, `test_collections_presenter`,
  delete/rename context-menu and rename-delegate e2e)
- [x] All tests have explicit timeout markers — module `pytestmark` timeout(60)
- [x] No merge conflicts
- [x] Syntax is valid
- [x] Types are correct (if applicable) — PYPOST-1013 touch points cleaned;
  `make typecheck` still reports 219 vs baseline 218 from pre-existing
  line-shift drift outside this task (committed HEAD was already 221 before
  cleanup; this step removed the export-actions `UserRole` pair and the new
  export-callback narrowing error)

## Notes

- `make lint` is green; flake8 scope is `pypost/` only.
- Unrelated working-tree leftovers (e.g. PYPOST-1005 docs/tests) were left
  untouched; they do not fail flake8 for this change set.
- Context-menu action counts remain 3 (collection) / 4 (request) after cleanup.
