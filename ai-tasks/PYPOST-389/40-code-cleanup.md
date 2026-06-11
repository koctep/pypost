# PYPOST-389: Code Cleanup

## Lint / format

- Docstring update only (`PYPOST-93` → `PYPOST-389`); no production code changes.
- Existing style preserved.

## Verification

- `python -m unittest tests.test_collections_presenter.TestCollectionsPresenter.test_restore_tree_state_skips_stale_saved_collection_ids` — pass (venv).

## Result

No cleanup issues.
