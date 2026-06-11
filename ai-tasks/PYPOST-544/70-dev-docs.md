# PYPOST-544: Dev Docs

## Updates

- `doc/dev/encryption_key_migration.md` — Settings **Re-encrypt all environments** section documents
  that the result dialog shows **Re-encrypted** and **Reused** counts when `reencrypt_stats` is
  present on the migration report.

## Operator guidance

After re-encrypt from Settings, check the result dialog for:

- **Re-encrypted** — hidden values that received a new envelope
- **Reused** — envelopes kept unchanged (e.g. already on active `kid`)

Same semantics as CLI `reencrypt_stats.encrypted_count` / `reused_count`.

## Related docs

- Parent runbook: [encryption_key_migration.md](../../doc/dev/encryption_key_migration.md)
- GUI tests: [gui_testing.md](../../doc/dev/gui_testing.md)
