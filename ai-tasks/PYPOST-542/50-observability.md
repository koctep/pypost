# PYPOST-542: Observability

## Logging

| Event | Level | Fields |
| --- | --- | --- |
| `encryption_migration_inventory_built` | INFO | `v1_envelope_count`, `v2_envelope_count` |
| `encryption_migration_operation_started` | INFO | `operation=upgrade_v2` |
| `encryption_migration_operation_skipped` | INFO | `reason=already_v2` |
| `encryption_migration_operation_completed` | INFO | success / error counts |

## CLI / JSON output

Human and JSON reports include `v1_envelopes` and `v2_envelopes` in inventory.

## Metrics

No new Prometheus counters; reuse existing encrypt/decrypt metrics on save path.
