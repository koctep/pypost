# PYPOST-525: Technical Debt Analysis

## Shortcuts Taken

None for PYPOST-525. This task pays down TD-1 from
[PYPOST-487](../PYPOST-487/60-tech-debt.md) by replacing private `_env_adapter` access in
migration with `StorageManager.load_environments_with_errors()`.

## Code Quality Issues

Minor, acceptable duplication:

- `load_environments()` and `load_environments_with_errors()` each implement a per-item
  deserialize loop. A shared private helper could reduce duplication but was intentionally
  deferred to keep desktop `load_environments()` behavior isolated and regression-safe.
- `EncryptionMigrationService._read_raw_environments()` still reads `environments.json` for
  inventory scans without decrypt (TD-2 from PYPOST-487).

## Missing Tests

Coverage is adequate for this task:

- Four new storage API tests plus UI regression (`load_environments()` unchanged on partial
  failure).
- Migration coupling guard (`test_deserialize_all_uses_public_storage_api`).
- Existing verify/re-encrypt/encrypt-plaintext tests pass without assertion changes.

No additional scenarios identified as blocking.

## Performance Concerns

None. Migration may read `environments.json` twice per operation (inventory scan + deserialize
via storage) — same as pre-PYPOST-525 behavior when `_deserialize_all` also read raw JSON
separately from inventory. TD-2 consolidation remains a future optimization, not a regression.

## Follow-up Tasks

| ID | Priority | Description | Jira |
| --- | --- | --- | --- |
| TD-2 | Low | Unify inventory scan and decrypt load to avoid duplicate file reads in migration | PYPOST-487 debt; not expanded here |
| TD-3 | Low | Skip bulk re-encrypt when inventory shows no ciphertext to rotate | PYPOST-487 debt |
| — | Low | Optional refactor: extract shared deserialize loop for `load_environments` and `load_environments_with_errors` | No ticket; only if both methods evolve together |

No new follow-up Jira issues required for PYPOST-525 completion.
