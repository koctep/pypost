# PYPOST-329: Code Cleanup

## Lint and format

- New test module follows existing `unittest` + `QApplication` patterns.
- No production code changes; linters pass on `tests/test_collection_tree_actions.py`.

## Test structure

- Shared `_patch_menu` context manager reduces duplication across seven cases.
- Fake request manager and state manager kept local to avoid cross-test coupling.

## Verification

- `python -m unittest tests.test_collection_tree_actions -v` — all pass.
- `python -m unittest tests.test_collections_presenter -v` — no regressions.
