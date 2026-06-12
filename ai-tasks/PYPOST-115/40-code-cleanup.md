# PYPOST-115: Code Cleanup

## Lint / format

- No new linter issues in `mixins.py` or `test_variable_hover.py`.
- Line length within 100 characters.

## Structure

- Extracted `_resolve_single_level_reference` to keep `get_variable_value` readable.
- Reused core tokenizer helpers; no duplicate regex.

## Tests

- `make test` — variable hover tests pass.
