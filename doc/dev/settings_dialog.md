# Settings Dialog — Alert Configuration (PYPOST-439)

## Overview

The Settings dialog (`pypost/ui/dialogs/settings_dialog.py`) persists application
preferences to `settings.json` via `ConfigManager`. Under **Security / Logging**, operators
can configure retry-exhaustion alert delivery.

## Alert Fields

| UI label | `AppSettings` field | Default | Runtime consumer |
| --- | --- | --- | --- |
| Alert Log Path | `alert_log_path` | `None` | `AlertManager` in `main.py` |
| Alert Webhook URL | `alert_webhook_url` | `None` | `AlertManager` |
| Alert Webhook Auth Header | `alert_webhook_auth_header` | `None` | `AlertManager` |

When `alert_log_path` is `None`, `AlertManager` uses
`{user_data_dir("pypost")}/pypost-alerts.log` (see `platformdirs`).

## Webhook Authorization — UI Safety

- The auth field uses **password echo** (`QLineEdit.EchoMode.Password`).
- On dialog open, the stored authorization value is **never** copied into the field.
- Placeholder text:
  - **Configured** — "Leave blank to keep configured value"
  - **Not configured** — "Bearer <token>"
- **Save behavior:**
  - Non-empty field → saves entered value
  - Empty field + existing stored value → keeps stored value
  - **Remove stored authorization header** checkbox (shown only when a value exists) →
    clears the field on save
- Authorization values are not written to application logs from Settings code paths.

## Persistence

Saved through `SettingsDialog.accept()` → `MainWindow.open_settings()` →
`ConfigManager.save_config()`. Fields are optional; empty strings become `None`.

## Limitation

`AlertManager` is created once at startup in `main.py`. Changing alert settings in the
dialog updates persistence but does not reconfigure the live instance until the
application restarts.

## Tests

`tests/test_settings_dialog.py`:

- `TestSettingsDialogAlertSettings` — load/save, echo mode, keep/clear auth
- `TestResolveWebhookAuthHeader` — pure helper unit tests

See also `doc/dev/gui_testing.md`.
