# PYPOST-132: Code Cleanup

## Lint / format

- No new linter warnings in changed files.
- Line length within 100 characters.

## Review notes

- No unused imports added.
- Cache helpers are private methods on `VariableAwareTableWidget`.
- Test patches `resolve_text` at the widget import site for stable mocking.

## Status

Clean — ready for review.
