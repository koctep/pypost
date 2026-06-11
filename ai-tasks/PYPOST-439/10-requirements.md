# PYPOST-439: Expose alert settings in Settings UI

## Goals

Operators can configure alert log path and webhook delivery from the Settings dialog
without editing `settings.json` manually.

## User Stories

- As an operator, I want to set the alert log file path in Settings so retry-exhaustion
  alerts are written where I expect.
- As an operator, I want to configure webhook URL and authorization in Settings so alerts
  can reach my incident channel.
- As an operator, I want webhook authorization values masked in the UI so secrets are not
  displayed on screen after they are saved.

## Definition of Done

| ID | Criterion |
| --- | --- |
| AC-1 | Settings dialog exposes editable **Alert Log Path** bound to `AppSettings.alert_log_path`. |
| AC-2 | Settings dialog exposes **Alert Webhook URL** bound to `AppSettings.alert_webhook_url`. |
| AC-3 | Settings dialog exposes **Alert Webhook Auth Header** with password echo; stored value is not shown on load. |
| AC-4 | Saving with an empty auth field keeps an existing stored header; operator can remove it explicitly. |
| AC-5 | Empty alert log path persists as `None` (platform default at runtime). |
| AC-6 | Qt tests cover load/save and auth masking semantics. |

## Scope

**In scope:** `SettingsDialog`, `tests/test_settings_dialog.py`, developer documentation.

**Out of scope:** Rebuilding `AlertManager` on settings save; webhook delivery changes;
manual QA checklist.

## Q&A

*(No open questions.)*
