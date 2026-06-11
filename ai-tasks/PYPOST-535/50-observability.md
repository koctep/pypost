# PYPOST-535: Observability

## Logging

| Event | Level | Fields |
| --- | --- | --- |
| `save_environments_completed` | INFO | `encrypted_count`, `reused_count` (aggregate) |
| `encryption_migration_save_completed` | INFO | `encrypted_count`, `reused_count` |
| `environment_serialized` | INFO | unchanged per-env `encrypted_count`, `reused_count` |

## CLI / JSON

- Human output adds `reencrypt_stats:` block on rewrite commands.
- `--json` adds `reencrypt_stats` object when stats are available.

## Metrics

No new Prometheus counters. Reuse remains observable via logs and migration CLI output.

## Verification

- [x] Filter `encryption_migration_save_completed` for batch rotation audits
- [x] Assert on `reencrypt_stats` in CI via `re-encrypt --json`
