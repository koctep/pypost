# PYPOST-426: Code Cleanup

## Changes

- Added `AppSettings` import in alphabetical order (`core` block, then `models`, then `ui`).
- Annotated `MainWindow.apply_settings` parameter.

## Lint / format

No new lint issues introduced. Import order follows existing `pypost` grouping.

## Out of scope

- Keyword-only `*` separator (presenters use typed positional; consistency chosen).
- Runtime validation of `settings` type.
