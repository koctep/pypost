# PYPOST-330: Code Cleanup

## Lint and format

- New test module follows existing `unittest` + `QApplication` patterns.
- No production code changes.

## Test structure

- `_delete_via_menu` context manager centralizes menu + index patching.
- Fake managers kept local; metrics use `MagicMock` for call assertions.

## Verification

- `python -m unittest tests.test_collection_tree_delete_confirmation -v` — all pass.
- `python -m unittest tests.test_collection_tree_actions -v` — no regressions.
