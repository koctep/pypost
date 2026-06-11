# PYPOST-342: Code Cleanup

## Lint

No production code changed. New test modules follow existing patterns:

- Module-level `pytestmark = pytest.mark.timeout(60)`
- Patch targets at `pypost.ui.presenters.collection_tree_actions`
- Shared helpers in `tests/helpers/collections_tree.py`

## Formatting

- Line length ≤ 100 characters
- LF line endings, UTF-8, trailing whitespace removed

## Verification

Run focused rename GUI tests and full `make test` before close.
