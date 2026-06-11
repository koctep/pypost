# PYPOST-536: Code Cleanup

## Lint and format

- No new lint issues in touched modules.
- Removed duplicate regex definition from `mixins.py`; single import from tokenizer.

## Files reviewed

| File | Notes |
| --- | --- |
| `pypost/core/template_expression_tokenizer.py` | Public export rename only |
| `pypost/ui/widgets/mixins.py` | Alias + import |
| `tests/test_variable_hover.py` | Parity and nested hover tests |

## Dead code

- None removed beyond the local `EXPRESSION_PATTERN` compile.
