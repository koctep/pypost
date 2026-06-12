# PYPOST-105: Code Cleanup

## Actions

- Extracted `_should_outdent_for_closing_bracket` and `_outdent_line_start` from monolithic handler.
- No flake8 issues introduced in `code_editor.py` or `test_code_editor.py`.

## Verification

- `make lint` — clean for touched modules.
