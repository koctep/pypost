# PYPOST-113: Code Cleanup

## Lint and format

- Removed unused `re` import from `mixins.py`.
- No new lint issues in touched modules.

## Files reviewed

| File | Notes |
| --- | --- |
| `pypost/core/template_expression_tokenizer.py` | New exports + helpers |
| `pypost/ui/widgets/mixins.py` | Import shared pattern; use helpers |
| `tests/test_template_expression_tokenizer.py` | Plain pattern contract tests |

## Dead code

- Removed local `VARIABLE_PATTERN = re.compile(...)` from `mixins.py`.
