# PYPOST-545: Dry-run projected reencrypt_stats for migration CLI

## Goals

Operators use `--dry-run` on `re-encrypt`, `encrypt-plaintext`, and `upgrade-v2` to preview
inventory changes before writing. PYPOST-535 added live `reencrypt_stats` on rewrite commands,
but dry-run omitted them. Surfacing projected encrypt/reuse counts lets operators confirm how
much work a rotation will perform without committing changes.

## Programming Language

Python 3.10+

## User Stories

- As an operator running `re-encrypt --dry-run` before key rotation, I want projected
  `encrypted_count` and `reused_count` so I can estimate rewrite scope.
- As a CI maintainer, I want `--json` dry-run output to include `reencrypt_stats` for scripted
  assertions.
- As a maintainer, I want dry-run stats to match what a live run would report for the same data.

## Definition of Done

- Dry-run on rewrite commands populates `reencrypt_stats` on `MigrationReport`.
- Human CLI output and `--json` include the same stats shape as live rewrite commands.
- Service and CLI tests assert projected counts for kid rotation and plaintext encrypt paths.
- Developer documentation reflects dry-run stats behavior.

## Out of Scope

- Settings UI migration dialog.
- New metrics backends.

## Acceptance Criteria

1. `re-encrypt --dry-run` with a historical `kid` reports non-zero `encrypted_count`.
2. `encrypt-plaintext --dry-run` reports `encrypted_count` equal to plaintext hidden count.
3. `--json` dry-run payload includes `reencrypt_stats` object.
4. On-disk data is unchanged after dry-run.
5. Existing encryption migration tests pass.
