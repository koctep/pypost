# Settings Dialog

## Overview

The Settings dialog (`pypost/ui/dialogs/settings_dialog.py`) persists application
preferences to `settings.json` via `ConfigManager`.

Since PYPOST-598, the dialog is a **thin coordinator** that composes domain section builders
under `pypost/ui/widgets/settings/`. Since PYPOST-1145, sections are grouped into categorized
`QTabWidget` pages. Callers and tests still import `SettingsDialog` from
`settings_dialog.py`; widget attributes remain on the dialog instance for backward-compatible
test access.

### Tabbed layout (PYPOST-1145)

`SettingsDialog` hosts a `settings_tabs` `QTabWidget` (`SETTINGS_TABS` /
`pypost_settings_tabs`) with Save/Cancel below the tab strip.

| Tab | Sections | User-guide alignment |
| --- | --- | --- |
| **General** | `EditorSettingsSection` | Editor and appearance |
| **Requests & Retries** | `RequestSettingsSection`, `RetryPolicySection` | Requests; retries |
| **Network** | `ServerBindSettingsSection`, `WebSocketSettingsSection` | MCP/metrics; WebSocket |
| **Security & Alerts** | `SecurityAlertSection` | Retries and alerts (logging/webhook) |
| **Encryption** | `EncryptionConfigSection`, `EncryptionMigrationSection` | Environment encryption |

Tests locate widgets across tabs via `form_layout_index_of(widget)` or
`tab_form_layout(page)` for per-tab ordering assertions.

### Section modules (PYPOST-598)

| Module | Domain |
| --- | --- |
| `editor_section.py` | Application font size, JSON indent, theme |
| `request_section.py` | Request timeout, confirm-before-overwrite |
| `server_bind_section.py` | MCP/metrics host and port, bind validation |
| `encryption_config_section.py` | Environment encryption mode, key source, fallback |
| `encryption_migration_section.py` | Verify / re-encrypt / encrypt-plaintext actions |
| `retry_policy_section.py` | Default retry policy, retryable status codes |
| `security_alert_section.py` | Security/logging header, hidden-key logging, alerts |
| `websocket_section.py` | WebSocket limits, heartbeat, reconnect, probe defaults |

`accept()` orchestrates validation (`server_bind`, `retry_policy`) then merges
`collect_fields()` from each section into one `AppSettings`.

Public helpers (`parse_env_encryption_enabled_from_mode`, `ENCRYPTION_MODE_*`,
`KEY_SOURCE_*`, `_resolve_webhook_auth_header`, validation/migration UI functions) are
re-exported from `settings_dialog.py` for tests and patch targets.

## Alert Configuration (PYPOST-439)

Under **Security / Logging**, operators can configure retry-exhaustion alert delivery.

## Alert Fields

| UI label | `AppSettings` field | Default | Runtime consumer |
| --- | --- | --- | --- |
| Alert Log Path | `alert_log_path` | `None` | `AlertManager` (startup + settings save) |
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

## Runtime reload (PYPOST-621)

`AlertManager` is created at startup in `main.py`. When the operator saves alert field
changes in Settings, `MainWindow.open_settings()` closes the previous instance, builds a
new `AlertManager` from the saved `AppSettings`, and propagates it to `TabsPresenter` so
subsequent requests use the updated log path and webhook configuration.

## MCP and metrics bind address validation

On Save, `ServerBindSettingsSection.validate()` (called from `SettingsDialog.accept()`)
validates MCP and metrics host/port fields via `pypost/core/bind_address_validation.py`
before other checks:

- **Hosts** — non-empty after trim; valid IPv4/IPv6 literal or hostname (label rules).
- **Ports** — integer in 1024–65535 (defense in depth; spinboxes use the same range).

Invalid input blocks persistence:

- `new_settings` is not set; dialog stays open.
- `show_invalid_bind_address` shows a warning (`QMessageBox.warning`).
- WARNING log: `bind_address_settings_validation_failed field=<label> reason=<reason>`.

Reasons: `empty`, `invalid_format`, `out_of_range`.

## Retryable status codes validation

On Save, `RetryPolicySection.validate()` parses the retryable status codes line edit via
`parse_retryable_status_codes`. Invalid input blocks persistence:

- `new_settings` is not set; dialog stays open.
- `show_invalid_retryable_status_codes` shows a warning (delegates to `QMessageBox.warning`).
- A structured WARNING is logged:
  `retryable_codes_settings_validation_failed reason=<empty_segment|invalid_token|out_of_range>`.

Parser rules and messages are defined in `pypost/models/retry.py` (PYPOST-423).

## Request timeout persistence

`AppSettings.request_timeout` (default 60 seconds) is edited via the timeout spinbox.
Save path: `SettingsDialog.accept()` → `MainWindow.open_settings()` →
`ConfigManager.save_config()`.

Restart-level integration test (PYPOST-445): `tests/test_settings_persistence.py` —
`test_request_timeout_survives_settings_dialog_save_and_restart` drives the dialog save path,
writes JSON via `ConfigManager`, simulates restart with a fresh `ConfigManager`, and asserts
the spinbox reflects the persisted value on reopen.

Direct ConfigManager round-trip (without dialog): `TestConfigManagerPersistence.test_save_then_load_roundtrip`.

## Tests

`tests/test_settings_dialog.py`:

- `TestSettingsDialogRequestTimeout` — spinbox layout, load, accept output
- `TestSettingsDialogAlertSettings` — load/save, echo mode, keep/clear auth
- `TestSettingsDialogBindAddressValidation` — blocked save on invalid host, valid save path
  (PYPOST-151)
- `TestSettingsDialogRetryableCodesValidation` — blocked save + warning on invalid codes
  (PYPOST-444)
- `TestResolveWebhookAuthHeader` — pure helper unit tests

`tests/test_settings_dialog_tabbed_layout.py` (PYPOST-1145):

- Tab labels, `SETTINGS_TABS` identity, and per-tab section placement

`tests/test_settings_persistence.py`:

- `test_request_timeout_survives_settings_dialog_save_and_restart` — dialog save + restart
  (PYPOST-445)

Parser unit tests: `tests/test_retryable_status_codes_parse.py`,
`tests/test_bind_address_validation.py` (PYPOST-151).

See also `doc/dev/gui_testing.md`. Agent e2e settle after opening Settings
(real modal, not patched `exec`): [agent_dialog_settle.md](agent_dialog_settle.md).
