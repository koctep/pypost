# PYPOST-532: Code Cleanup

## Lint and format

- New test follows existing helpers (`_patch_dirs`, `_write_settings`, `_import_cli_main`).
- Imports localized inside test (`build_key_id`) consistent with `test_cli_re_encrypt_dry_run`.

## Scope check

- Single test function added; no CLI or service changes.

## Review

Ready for observability and tech-debt review.
