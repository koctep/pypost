# PYPOST-345: Code Cleanup

## Lint

No production code changed. New test module follows existing patterns:

- Module-level `pytestmark = pytest.mark.timeout(60)`
- Helpers in `tests/helpers/collections_tree.py`
- Patch `QMenu` only; `view.edit` runs for real

## Formatting

- Line length ≤ 100 characters
- LF line endings, UTF-8, trailing whitespace removed

## Verification

Focused e2e module and full `make test` pass.
