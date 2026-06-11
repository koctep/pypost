# PYPOST-487 — Developer Documentation

> Team Lead: team_lead
> Date: 2026-06-11
> Sprint: (current)

---

## 1. What Changed and Why

PYPOST-487 adds operator migration tooling for environment encryption at rest: inventory and verify,
bulk re-encryption after key rotation, and one-shot encryption of plaintext hidden values. The
migration layer orchestrates existing `StorageManager` / `EnvironmentVariablesAdapter` paths without
changing envelope format, codec contracts, or key provider behavior.

Operators get a scriptable CLI and a consolidated runbook (rollout stages, scenario procedures,
fallback matrix). Developers get `EncryptionMigrationService` as a single facade over storage I/O.

---

## 2. New and Updated Modules

- `pypost/core/encryption_migration.py` (new)
  - `EnvironmentInventory`, `MigrationReport`, `EncryptionMigrationService`
  - `backup_environments_file()` — timestamped sibling backup
- `scripts/encryption_migrate.py` (new)
  - Subcommands: `verify`, `report`, `re-encrypt`, `encrypt-plaintext`
  - Loads `AppSettings` via `ConfigManager`; uses `StorageManager`

No changes to `EnvironmentSecretsCodec`, `KeyProvider`, or `build_key_provider()`.

---

## 3. Documentation Updated

- `doc/dev/encryption_key_migration.md` (new)
  - Operator runbook: rollout stages 0–4, scenarios M1–M8, CLI usage, verification checklist,
    fallback matrix, troubleshooting, developer API summary
- `doc/dev/environment_encryption_at_rest.md`
  - Cross-link to migration runbook in overview-adjacent flow (rotation section references M7)
- `doc/dev/README.md` — navigation entry for encryption key migration

---

## 4. Configuration Summary

No new settings or environment variables. Migration respects existing encryption policy and key
source chain from `AppSettings` and `PYPOST_ENV_ENCRYPTION_*` overrides.

| CLI flag | Default | Effect |
| --- | --- | --- |
| `--dry-run` | off | Full decrypt; projected inventory; no write |
| `--no-backup` | backup on | Skip timestamped `environments.json` copy before write |

---

## 5. Testing

Focused suites (15 tests):

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_encryption_migration.py \
  tests/test_encryption_migrate_cli.py
```

Full regression:

```bash
make test
```

---

## 6. Related Tickets

- `PYPOST-447` — encryption-at-rest foundation
- `PYPOST-481` — user-facing encryption settings
- `PYPOST-483` — multi-source key provider chain and rotation
- `PYPOST-486` — async environment storage when encryption enabled
- `PYPOST-487` — migration service, CLI, and operator runbook (this task)
- `PYPOST-500+` — vault backend (Stage 4 reference in runbook)
