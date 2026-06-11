# PYPOST-527 — Developer Documentation

> Date: 2026-06-11

---

## 1. What Changed and Why

Settings dialog now exposes **Verify encryption** and **Re-encrypt all environments** for
operators who configure encryption in the desktop app. Actions delegate to
`EncryptionMigrationService` — the same service used by `scripts/encryption_migrate.py` — with
confirmation before bulk re-encrypt and backup enabled by default.

## 2. New and Updated Modules

- `pypost/ui/dialogs/settings_dialog.py`
  - Optional `storage` kwarg; migration section buttons; `_encryption_settings_from_form()`
  - `_on_verify_encryption()`, `_on_re_encrypt_environments()`, `_format_migration_report()`
- `pypost/ui/main_window.py`
  - `open_settings()` passes `storage=self.storage`
- `tests/test_settings_encryption_migration_ui.py` — UI delegation and confirmation tests

No changes to `EncryptionMigrationService`, storage, or CLI.

## 3. Documentation Updated

- `doc/dev/encryption_key_migration.md` — Settings listed as operator surface; M7 UI path

## 4. Configuration Summary

No new settings fields. Actions use encryption fields from the Settings form at click time.

## 5. Testing

```bash
pytest tests/test_settings_encryption_migration_ui.py -v
pytest tests/test_settings_encryption.py tests/test_encryption_migration.py -v
```

## 6. Operator Notes

- Verify is read-only; re-encrypt requires confirmation and creates a timestamped backup.
- Save Settings separately if you want encryption policy persisted to `settings.json`.
- For `encrypt-plaintext` or `--dry-run`, use the CLI.
