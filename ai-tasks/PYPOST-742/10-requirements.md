# PYPOST-742: Requirements

Replace stdout `print()` error reporting in configuration management with stdlib logging so
config failures are captured by pytest log guardrails and support log bundles.

`StyleManager` already uses `logger`; three remaining `print()` calls were in `ConfigManager`.

## Definition of Done

- No `print()` in `pypost/core/config_manager.py` for error paths
- ERROR logs use structured key=value messages
- Tests assert ERROR logs on load/save failure
