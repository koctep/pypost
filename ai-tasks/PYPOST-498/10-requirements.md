# PYPOST-498: Refactor environment list inline editing

## Goals

Inline environment rename validation currently relies on `itemChanged` signal blocking and
message boxes to revert invalid names. This is fragile and noisy. Provide cleaner inline
validation at edit-commit time without modal dialogs.

## Definition of Done

- Environment list inline rename uses a custom item delegate for validation.
- Invalid renames (empty, duplicate) are rejected without QMessageBox.
- Valid renames update the environment model and log `environment_renamed`.
- Existing rename behaviour covered by automated tests.
