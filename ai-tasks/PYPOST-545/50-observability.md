# PYPOST-545: Observability

## Logging

Extended `encryption_migration_dry_run_completed` with `projected_reused_count`:

```
encryption_migration_dry_run_completed operation=re_encrypt
  projected_encrypted_count=1 projected_reused_count=0 active_kid=...
```

Per-environment `environment_serialized` logs still emit during `project_save_stats` simulation
(same as live save path).

## Metrics

No new Prometheus counters — dry-run remains log-only per PYPOST-535 scope.

## Tests

- Service dry-run tests assert `report.reencrypt_stats`.
- CLI human + JSON dry-run tests assert output shape.
