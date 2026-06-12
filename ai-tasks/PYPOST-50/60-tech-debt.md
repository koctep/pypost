# PYPOST-50: Technical Debt Review

## Blockers

None. Protocol extraction is complete; behavior unchanged.

## Non-blockers (follow-up)

### Split collection vs environment storage modules

`StorageManager` still owns both collection JSON files and `environments.json` I/O. A future
refactor could split modules while keeping `StorageInterface` as the facade.

**Jira:** Not created — low impact, no product regression risk; defer until a second backend
is needed.

### EncryptionMigrationService path coupling

`EncryptionMigrationService` reads `storage.environments_file` directly. A future improvement
could add `get_environments_path()` to the protocol if alternate layouts appear.

**Jira:** Not created — acceptable for current single-file layout.

## Audit resolution

- PYPOST-40 R8 — **Resolved** by this task.
