# PYPOST-527: Technical Debt Analysis

## Shortcuts Taken

- **Synchronous UI-thread migration** — verify and re-encrypt run on the Qt UI thread like a
  direct CLI invocation. Acceptable for typical desktop datasets; large files may freeze Settings
  briefly.
- **Duplicate report formatter** — `_format_migration_report` in `settings_dialog.py` parallels
  CLI `_format_inventory` in `scripts/encryption_migrate.py` to avoid importing Qt from scripts or
  scripts from UI.
- **encrypt-plaintext not in Settings** — CLI and service support it; UI exposes verify +
  re-encrypt only per TD-3 scope.

## Code Quality Issues

- None blocking close. Optional follow-up: shared text formatter in `encryption_migration.py`
  (no Qt dependency).

## Missing Tests

- Integration test with real `StorageManager` + Fernet fixture through button click (covered at
  service layer in `test_encryption_migration.py`; UI tests mock service).
- MainWindow e2e asserting `SettingsDialog(..., storage=...)` wiring (low risk one-line change).

## Performance Concerns

- Long re-encrypt on UI thread — same as CLI; progress feedback deferred.

## Architecture Deviations

| Planned | Delivered | Impact |
| --- | --- | --- |
| Optional Settings UI (PYPOST-487) | Verify + re-encrypt only | encrypt-plaintext still CLI-only |

## Follow-up Tasks

| ID | Priority | Task | Rationale |
| --- | --- | --- | --- |
| TD-1 | Low | Add Settings action for encrypt-plaintext | Parity with CLI M4 scenario | [PYPOST-640](https://pypost.atlassian.net/browse/PYPOST-640) |
| TD-2 | Low | Extract shared migration report text formatter | DRY with CLI | [PYPOST-641](https://pypost.atlassian.net/browse/PYPOST-641) |
| TD-3 | Low | Background worker for bulk re-encrypt from UI | Avoid UI freeze on large files | [PYPOST-642](https://pypost.atlassian.net/browse/PYPOST-642) |

## Review

No blockers. SAFE TO CLOSE. TD-3 from PYPOST-487 is resolved by this task.
