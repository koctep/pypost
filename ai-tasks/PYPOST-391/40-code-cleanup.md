# PYPOST-391: Code Cleanup

## Lint / format

- Docstring update only (`PYPOST-95` → `PYPOST-391`); no production code changes.
- Existing style preserved.

## Verification

- `python -m unittest tests.test_collections_presenter.TestCollectionsPresenter.test_restore_tree_state_expands_only_collections_in_saved_list` — pass (venv).

## Result

No cleanup issues.
