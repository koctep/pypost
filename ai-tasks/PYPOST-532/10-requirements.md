# PYPOST-532: CLI test for encrypt-plaintext --dry-run

## Goals

Close the test gap identified in PYPOST-487 TD-9: service-layer dry-run for
`encrypt_plaintext_hidden` is covered, but the `encryption_migrate.py` CLI wrapper lacked a
matching test for `encrypt-plaintext --dry-run`.

## Programming Language

Python 3.10+

## User Stories

- As a maintainer, I want a CLI test for `encrypt-plaintext --dry-run` so regressions in the
  argparse wiring or stdout formatting are caught alongside `re-encrypt --dry-run`.

## Definition of Done

- New test in `tests/test_encryption_migrate_cli.py` exercises `encrypt-plaintext --dry-run`.
- Assertions cover exit code, `dry_run: true` in human output, projected inventory counts, and
  that on-disk plaintext is unchanged after dry run.
- Existing CLI and service tests continue to pass.

## Out of Scope

- Changes to `encryption_migrate.py` or `EncryptionMigrationService` (behavior already correct).
- JSON-mode dry-run assertions (optional follow-up).

## Acceptance Criteria

1. `encrypt-plaintext --dry-run --no-backup` exits 0 with plaintext hidden values on disk.
2. Stdout includes `dry_run: true`, `plaintext_hidden: 0`, `encrypted_envelopes: 1`, and active
   `kid` in histogram (parity with service test and `re-encrypt --dry-run` CLI test).
3. `environments.json` still contains the original plain hidden string after dry run.
