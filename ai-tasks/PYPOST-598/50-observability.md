# PYPOST-598: Observability

## Summary

Structural refactor only — no new log events or metrics. All existing Settings dialog log
strings and logger names are preserved.

## Logger name

All Settings validation and migration events continue to emit under
`pypost.ui.dialogs.settings_dialog` (even when code lives in section modules), so log
queries and test `caplog` assertions remain stable.

## Preserved log events

| Event | Location (post-refactor) |
| --- | --- |
| `bind_address_settings_validation_failed field=… reason=…` | `server_bind_section.py` |
| `retryable_codes_settings_validation_failed reason=…` | `retry_policy_section.py` |
| `settings_encryption_verify_started` | `encryption_migration_section.py` |
| `settings_encryption_verify_completed success=… error_count=…` | `encryption_migration_section.py` |
| `settings_encryption_re_encrypt_started/cancelled/completed` | `encryption_migration_section.py` |
| `settings_encryption_encrypt_plaintext_started/cancelled/completed` | `encryption_migration_section.py` |
| `settings_encryption_migration_worker_failed error=…` | `encryption_migration_section.py` |

## Patch targets (unchanged)

Tests patch module-level helpers on `pypost.ui.dialogs.settings_dialog`:

- `show_invalid_bind_address`
- `show_invalid_retryable_status_codes`
- `show_migration_result`
- `confirm_re_encrypt_environments` / `confirm_encrypt_plaintext_hidden` (via constructor DI)

Section modules lazy-import these from `settings_dialog` where needed to keep patch paths valid.

## PII / secrets

- Webhook auth values are not logged from Settings code paths (unchanged).
- Encryption migration reports shown in UI only; errors logged without key material.

## Checklist

- [x] No log message format changes
- [x] Logger name unchanged (`pypost.ui.dialogs.settings_dialog`)
- [x] No new PII exposure paths introduced
- [x] Validation WARNING events still emitted on blocked save
