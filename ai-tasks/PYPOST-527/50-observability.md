# PYPOST-527: Observability Implementation

## Logging Implementation

### Added Logs

New structured logs in `pypost/ui/dialogs/settings_dialog.py`:

- **INFO**: `settings_encryption_verify_started`
- **INFO**: `settings_encryption_verify_completed` — `success`, `error_count`
- **INFO**: `settings_encryption_reencrypt_cancelled` — operator declined confirmation
- **INFO**: `settings_encryption_reencrypt_started`
- **INFO**: `settings_encryption_reencrypt_completed` — `success`, `backup`, `error_count`

Existing `EncryptionMigrationService` logs (`encryption_migration_verify_*`,
`encryption_migration_operation_*`, etc.) fire unchanged when UI invokes the service.

### Log Structure

- Structured key=value fields consistent with migration and storage events
- No key material, ciphertext, or secret values in UI-layer logs
- Levels: INFO only at UI boundary; service emits WARNING/ERROR on failures

## Metrics Implementation

No new Prometheus metrics. Migration service adapter counters unchanged.

## Monitoring Integration

- [ ] Prometheus — unchanged
- [x] Log aggregation — filter on `settings_encryption_*` for desktop operator actions

## Validation Results

- [x] UI logs use stable event names
- [x] Failure paths log `success=false` with `error_count`
- [x] Service-layer detail remains in `encryption_migration` logger

## Notes

Result dialogs show operator-facing summaries only; full decrypt failure detail comes from
service `errors` in the dialog body, not duplicated in UI log lines.
