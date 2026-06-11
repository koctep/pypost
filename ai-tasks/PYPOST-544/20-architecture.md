# PYPOST-544: Architecture

## Context

- **PYPOST-535** — `MigrationReport.reencrypt_stats` populated on rewrite paths; CLI formats stats
  in `_format_inventory`.
- **PYPOST-527** — Settings dialog delegates to `EncryptionMigrationService`; `_format_migration_report`
  renders inventory for QMessageBox.

## Design

Extend `_format_migration_report(report)` to append two lines when `report.reencrypt_stats` is not
`None`:

```
Re-encrypted: {encrypted_count}
Reused: {reused_count}
```

Insert after backup path and before errors — same ordering as CLI human output.

## Components

| Component | Change |
| --- | --- |
| `settings_dialog._format_migration_report` | Append stats lines when present |
| `tests/test_settings_encryption_migration_ui.py` | Assert dialog body contains counts |

## Data Flow

```
Re-encrypt button → bulk_re_encrypt → MigrationReport(reencrypt_stats=...)
  → _show_migration_result → _format_migration_report → QMessageBox
```

No new types or service methods.

## Testing

- Mock `bulk_re_encrypt` to return report with `ReencryptStats(2, 1)`.
- Assert `QMessageBox.information` body contains both labels and values.

## Risks

None — read-only presentation of existing report field.
