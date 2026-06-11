# PYPOST-547: Observability

No new logging or metrics required. Existing caller-side log events are unchanged:

- `env_presenter`: `storage_save_failed`, `mcp_server_start_failed_ui`,
  `variable_set_request_no_env_selected`
- `main_window`: `metrics_server_start_failed_ui`
- `settings_dialog`: `settings_encryption_verify_*`, `settings_encryption_reencrypt_*`,
  `retryable_codes_settings_validation_failed`
- `request_save_orchestrator`: `save_request_overwrite_cancelled`, `save_request_stale_cancelled`

Dialog helpers remain presentation-only; observability stays in presenters and orchestrators.
