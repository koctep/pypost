# PYPOST-109: Code Cleanup

## Review

- `_should_format_pasted_json` is a module-level helper beside the threshold constant — easy to
  unit test and keeps `insertFromMimeData` readable.
- No new imports or dependencies.
- Existing paste branches unchanged for text at or below the threshold.

## Changes made

None beyond implementation — no dead code or unused imports introduced.
