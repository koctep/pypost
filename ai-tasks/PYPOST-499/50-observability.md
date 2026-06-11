# PYPOST-499: Observability

No new logs or metrics. Test asserts existing `storage_encryption_config_applied` INFO log
emitted by `EnvironmentVariablesAdapter.apply_encryption_settings` after `open_settings()`.
