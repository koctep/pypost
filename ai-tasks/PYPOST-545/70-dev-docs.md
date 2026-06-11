# PYPOST-545: Dev docs

## Updated

- `doc/dev/encryption_key_migration.md` — dry-run now includes projected `reencrypt_stats`.

## Operator note

Run `re-encrypt --dry-run` (or `--json`) before a live rotation to preview both kid histogram
and encrypt/reuse counts without modifying `environments.json`.
