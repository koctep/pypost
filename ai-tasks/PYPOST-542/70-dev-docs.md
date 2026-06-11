# PYPOST-542: Dev Docs

## Updated files

- `doc/dev/encryption_key_migration.md` — M9 scenario, `upgrade-v2` CLI, inventory fields,
  `upgrade_envelopes_to_v2()` API, troubleshooting.
- `doc/dev/environment_encryption_at_rest.md` — `encrypt_v2()` and migration note on v2 section.

## Operator entry point

```bash
python scripts/encryption_migrate.py upgrade-v2 [--dry-run] [--no-backup]
```
