# PYPOST-528: Skip no-op bulk_re_encrypt when kid histogram matches active key

## Goals

PYPOST-487 delivered `bulk_re_encrypt` to rewrite all environments so hidden values use the active
encryption key. When every hidden value is already encrypted with the active `kid` and there is no
plaintext hidden data, the operation still loads, decrypts, backs up, and saves the file — causing
unnecessary I/O with no functional change.

This task adds an inventory pre-check so `bulk_re_encrypt` returns success immediately without
backup or file writes when re-encryption would be a no-op.

## Programming Language

Python 3.10+

## User Stories

- As an operator who clicks **Re-encrypt all environments** when data is already on the active key,
  I want the operation to complete quickly without rewriting `environments.json`.
- As an operator running the CLI `re-encrypt` command on an already-migrated dataset, I want no
  backup file created when nothing would change.
- As a maintainer, I want the skip behavior to mirror `encrypt_plaintext_hidden` when there is
  nothing to do, with structured logging for observability.

## Definition of Done

- `bulk_re_encrypt` skips backup and save when inventory shows only the active `kid` and zero
  plaintext hidden values.
- `bulk_re_encrypt` still rewrites when plaintext hidden values exist or any envelope uses a
  non-active `kid`.
- Structured log emitted on skip (`reason=already_on_active_kid`).
- Automated tests cover skip and non-skip paths.
- Developer documentation updated for the early-exit behavior.

## Out of Scope

- Skipping when envelopes have empty `kid` (PYPOST-529).
- Progress feedback or background workers.
- Changes to `encrypt_plaintext_hidden` skip logic (already implemented).

## Acceptance Criteria

1. Given all hidden values encrypted with active `kid` and no plaintext, `bulk_re_encrypt` returns
   `success=True`, `backup_path=None`, and does not modify `environments.json`.
2. Given plaintext hidden values mixed with encrypted data, `bulk_re_encrypt` performs a full rewrite.
3. Given encrypted data under a historical `kid`, `bulk_re_encrypt` performs a full rewrite.
4. Dry-run and live paths both honor the pre-check.
