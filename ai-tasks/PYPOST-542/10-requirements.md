# PYPOST-542: v1 to v2 envelope re-encrypt migration

## Goals

PYPOST-541 added v2 envelope decrypt support. Operators still have v1 envelopes on disk from
runtime saves and earlier migrations. They need an explicit, safe path to normalize stored hidden
values to v2 without manual re-entry or ad-hoc file edits.

## Programming Language

Python 3.10+

## User Stories

- As an operator preparing for v2-only features, I want a bulk upgrade path from v1 to v2
  envelopes so on-disk data matches the newer schema.
- As an operator, I want dry-run and backup on the upgrade path so I can verify counts before
  writing.
- As a maintainer, I want runtime saves unchanged (still v1) until a separate decision, while
  migration tooling can write v2 deliberately.

## Definition of Done

- Migration service can rewrite v1 hidden envelopes to v2 fernet under the active key.
- Inventory reports `v1_envelopes` and `v2_envelopes` counts.
- CLI exposes `upgrade-v2` with `--dry-run` and `--no-backup`.
- Plain hidden strings are encrypted as v2 when present during upgrade.
- Operation skips when all hidden values are already v2 and none are plaintext.
- Tests cover service, codec `encrypt_v2`, and CLI paths.

## Out of Scope

- Changing default runtime `encrypt()` to emit v2.
- Settings UI button for v2 upgrade.
- Selective per-environment upgrade filters.

## Acceptance Criteria

1. `report` / inventory shows separate v1 and v2 envelope counts.
2. `upgrade-v2` rewrites v1 envelopes to `v=2` fernet and decrypt still succeeds.
3. `upgrade-v2 --dry-run` projects v2 counts without writing.
4. Second `upgrade-v2` run skips when already v2 (no backup, no mtime change).
5. All existing encryption migration tests pass.
