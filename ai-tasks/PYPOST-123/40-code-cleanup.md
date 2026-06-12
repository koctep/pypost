# PYPOST-123: Code Cleanup

## Lint / format

- No new linter warnings in changed files.
- Line length within 100 characters.

## Review notes

- Removed superseded `_resolve_single_level_reference`; logic consolidated in one helper.
- `visited` set passed by value on recursion (`seen | {name}`) — no mutation bugs.
- Tests patch `TOOLTIP_REFERENCE_MAX_DEPTH` for deterministic depth-limit assertion.

## Status

Clean — ready for review.
