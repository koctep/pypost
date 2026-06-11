# PYPOST-535: Dev Docs

## Updated

- `doc/dev/encryption_key_migration.md` — `reencrypt_stats` in CLI/JSON, kid-aware reuse note,
  `ReencryptStats` on `MigrationReport`.

## Operator summary

After `re-encrypt` or `encrypt-plaintext`, check `reencrypt_stats` for how many hidden values
were newly encrypted versus reused unchanged envelopes under the active `kid`.
