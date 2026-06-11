# PYPOST-529: Observability Implementation

## Logging Implementation

### Added Logs

In `pypost/core/encryption_migration.py`:

- **INFO**: `_log_inventory` includes `invalid_hidden_count` and `data_quality_error_count`
- **ERROR**: `encryption_migration_data_quality_errors count=<n>` on verify and rewrite abort

### Log Structure

- Structured key=value fields consistent with existing migration events
- Error messages name environment and key; no secret values logged

## Metrics Implementation

No new metrics. Inventory log fields sufficient for operator triage.

## Monitoring Integration

- [x] Filter `encryption_migration_data_quality_errors` to detect corrupt on-disk hidden shapes

## Validation Results

- [x] Tests assert data-quality error log via `caplog`
