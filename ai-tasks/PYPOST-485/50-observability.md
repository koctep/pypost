# PYPOST-485: Observability

## Logging

`environment_serialized` log line now includes `reused_count` alongside `encrypted_count`:

```text
environment_serialized env_name=... encryption_enabled=... encrypted_count=N reused_count=M total_variables=T
```

Operators can compare `encrypted_count` vs `reused_count` on repeated saves to confirm selective
re-encrypt is active.

## Metrics

| Metric | Change |
| --- | --- |
| `environment_value_encryptions_total` | Incremented only on new Fernet encrypt, not envelope reuse |
| `environment_value_decryptions_total` | Unchanged (load path only) |
| `environment_encryption_errors_total` | Unchanged |

Reuse is intentionally not a separate counter to avoid metric sprawl; log field suffices for
debugging save hot paths.

## Policy invalidation

`apply_encryption_settings` clears persisted snapshots and logs `storage_encryption_config_applied`
as before, preventing stale envelope reuse after policy changes.
