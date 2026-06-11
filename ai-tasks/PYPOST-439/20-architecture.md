# PYPOST-439 Architecture — Settings alert fields

## 1. Problem Summary

`AppSettings` persists `alert_log_path`, `alert_webhook_url`, and
`alert_webhook_auth_header`. Webhook URL fields were partially wired in
`SettingsDialog`, but `alert_log_path` was copied unchanged on save and the auth header
was shown in a plain `QLineEdit`.

## 2. Solution Overview

Extend `SettingsDialog` under the existing **Security / Logging** section:

| Field | Widget | Load | Save |
| --- | --- | --- | --- |
| Alert log path | `QLineEdit` | Show stored path or empty | Strip; empty → `None` |
| Webhook URL | `QLineEdit` | Show URL or empty | Strip; empty → `None` |
| Webhook auth | `QLineEdit` (Password echo) | Always empty; placeholder hints | See `_resolve_webhook_auth_header` |
| Remove auth | `QCheckBox` (only when stored) | Hidden when no stored auth | Checked → `None` |

Default log path placeholder uses `platformdirs.user_data_dir("pypost")` +
`pypost-alerts.log`, matching `AlertManager`.

### Auth resolution (`_resolve_webhook_auth_header`)

1. Remove checkbox checked → `None`
2. Non-empty entered text → new value
3. Empty + had stored auth → keep stored value
4. Empty + no stored auth → `None`

## 3. Files Changed

| File | Change |
| --- | --- |
| `pypost/ui/dialogs/settings_dialog.py` | UI fields, auth helper, save wiring |
| `tests/test_settings_dialog.py` | Load/save and helper unit tests |
| `doc/dev/settings_dialog.md` | Operator/dev reference (Step 7) |

## 4. Risks

| Risk | Mitigation |
| --- | --- |
| Secret shown in UI | Password echo; never populate auth field from settings |
| Accidental auth wipe | Keep-on-blank; explicit remove checkbox |
| Settings save does not reload `AlertManager` | Document as known limitation (pre-existing) |
