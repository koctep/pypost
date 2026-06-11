# PYPOST-374: Observability

Analysis-only task. No new metrics or log statements in dialog code.

## Existing dialog logging (documented for maintainers)

| Dialog | Logger | Events |
| --- | --- | --- |
| `settings_dialog.py` | `pypost.ui.dialogs.settings_dialog` | `settings_encryption_verify_started/completed`, `settings_encryption_reencrypt_*`, `retryable_codes_settings_validation_failed` |

Other dialogs (`about`, `hotkeys`, `save`, `env`, MCP viewers) rely on presenter-level or
widget-level logging rather than dialog-local loggers.

## Audit implications

- Settings encryption and retry validation paths already emit structured INFO/WARNING logs —
  no observability gap identified for this audit.
- Read-only MCP dialogs have no logging requirement; data is injected at open time from
  `env_presenter.py`.

No production log level changes recommended.
